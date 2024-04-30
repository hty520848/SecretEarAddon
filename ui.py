# ------------------------------------------------------
#
# UI
#
# ------------------------------------------------------
#  .XXX代表与该文件同级的文件，    ..XXX代表与带文件父目录同级的文件
from .public_operation import draw_font
import bpy
import os
import bpy.utils.previews
from .jiahou import *
from .damo import *
import bpy_extras
from bpy_extras.io_utils import ImportHelper
from .icon.icons import load_icons
from .icon.icons import clear_icons
from bpy.props import BoolProperty

import mathutils
import bmesh
from bpy_extras import view3d_utils
from bpy.types import SpaceView3D
import math
import time, functools

# 记录左右窗口视角的数据
left_last_dis = None
right_last_dis = None
left_last_rot = None
right_last_rot = None
left_last_loc = None
right_last_loc = None

# 记录之前窗口的context模式
prev_context = ''

# 镜像窗口属性栏是否显示
show_prop = False

# 打磨面板
class HUIER_PT_damo_R(bpy.types.Panel):

    bl_label = "耳样处理（右耳）"
    bl_idname = "HUIER_PT_damo_R"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    @classmethod
    def poll(cls, context):
        return context.scene.leftWindowObj == '右耳'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.separator()
        col.prop(context.scene, 'laHouDUR', text="蜡厚度")
        col.separator()
        col.prop(context.scene, 'localLaHouDu', text="局部蜡厚度限制")
        col = layout.column()
        col.active = context.scene.localLaHouDu
        col.prop(context.scene, 'maxLaHouDu', text="最大蜡厚度")
        col.separator()
        col.prop(context.scene, 'minLaHouDu', text="最小蜡厚度")

class HUIER_PT_damo_L(bpy.types.Panel):

    bl_label = "耳样处理（左耳）"
    bl_idname = "HUIER_PT_damo_L"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    @classmethod
    def poll(cls, context):
        return context.scene.leftWindowObj == '左耳'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene, 'laHouDUL', text="蜡厚度")
        col.separator()
        col.prop(context.scene, 'localLaHouDu', text="局部蜡厚度限制")
        col = layout.column()
        col.active = context.scene.localLaHouDu
        col.prop(context.scene, 'maxLaHouDu', text="最大蜡厚度")
        col.separator()
        col.prop(context.scene, 'minLaHouDu', text="最小蜡厚度")


# 局部或整体加厚面板


class HUIER_PT_LocalOrGlobalJiaHou(bpy.types.Panel):
    bl_label = "局部或整体加厚"
    bl_idname = "HUIER_PT_LocalOrGlobalJiaHou"
    bl_space_type  =  "PROPERTIES"
    bl_region_type  =  "WINDOW"
    bl_context="output"
    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'localThicking_offset', text="偏移值")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'localThicking_borderWidth', text="边框宽度")
        # layout.separator()
        # col = layout.column(align=True)
        # col.prop(context.scene, 'localThicking_circleRedius', text="圆环半径")

# 局部或整体加厚面板2


# class HUIER_PT_LocalOrGlobalJiaHou2(bpy.types.Panel):
#     bl_label = "局部或整体加厚"
#     bl_idname = "HUIER_PT_LocalOrGlobalJiaHou2"
#     bl_space_type = "PROPERTIES"
#     bl_region_type = "WINDOW"
#     bl_context = "view_layer"

#     def draw(self, context):
#         layout = self.layout
#         layout.separator()
#         col = layout.column(align=True)
#         col.prop(context.scene, 'localThicking_offset', text="偏移值")
#         layout.separator()
#         col = layout.column(align=True)
#         col.prop(context.scene, 'localThicking_borderWidth', text="边框宽度")

# 点面切割


class HUIER_PT_DianMianQieGe(bpy.types.Panel):
    bl_label = "选择工具"
    bl_idname = "HUIER_PT_DianMianQieGe"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'qieGeTypeEnum', text="选择工具")


class HUIER_PT_PlantCut(bpy.types.Panel):
    bl_label = "plant cut平面切割"
    bl_idname = "HUIER_PT_PlantCut"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"

    @classmethod
    def poll(cls, context):
        return context.scene.qieGeTypeEnum == 'OP1'

    def draw(self, context):
        layout = self.layout
        layout.separator()
        # layout.active = (context.scene.qieGeTypeEnum == 'OP1')
        col = layout.column(align=True)
        col.prop(context.scene, 'qiegesheRuPianYi', text="舍入偏移")
        layout.separator()


class HUIER_PT_StepCut(bpy.types.Panel):
    bl_label = "step vent阶梯状切割"
    bl_idname = "HUIER_PT_StepCut"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"

    @classmethod
    def poll(cls, context):
        return context.scene.qieGeTypeEnum == 'OP2'

    def draw(self, context):
        layout = self.layout
        layout.separator()
        # layout.active = (context.scene.qieGeTypeEnum == 'OP2')
        col = layout.column(align=True)
        col.prop(context.scene, 'qiegewaiBianYuan', text="外边缘平滑偏移")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'qiegeneiBianYuan', text="内边缘平滑偏移")


class HUIER_PT_MoJuTab(bpy.types.Panel):
    bl_label = ""
    bl_idname = "HUIER_PT_MoJuTab"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        col  = layout.split(factor=0.4)
        row = col.row(align=True)
        row.prop_tabs_enum(context.scene, 'tabEnum')


# 创建模具
class HUIER_PT_ChuangJianMuJu(bpy.types.Panel):
    bl_label = "创建模具"
    bl_idname = "HUIER_PT_ChuangJianMuJu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'HIDE_HEADER'}

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '参数'

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'muJuNameEnum', text="模具类型", icon='NONE')
        # layout.separator()
        # col = layout.column(align=True)
        # col.prop(context.scene, 'neiBianJiXian', text="内编辑线")
        # layout.separator()
        # col = layout.column(align=True)
        # col.prop(context.scene, 'waiBianYuanSheRuPianYi', text="外舍入偏移")
        # layout.separator()
        # col = layout.column(align=True)
        # col.prop(context.scene, 'neiBianYuanSheRuPianYi', text="内舍入偏移")

class HUIER_PT_MuJuPianYi(bpy.types.Panel):
    bl_label = "模具偏移"
    bl_idname = "HUIER_PT_MuJuPianYi"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'HIDE_HEADER'}

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.scene.tabEnum == '参数' and context.scene.muJuTypeEnum != 'OP2'
                and context.scene.muJuTypeEnum != 'OP5')

    def draw(self, context):
        layout = self.layout
        # layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'neiBianJiXian', text="内编辑线")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'waiBianYuanSheRuPianYi', text="外舍入偏移")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'neiBianYuanSheRuPianYi', text="内舍入偏移")


class HUIER_PT_MuJuHouDu(bpy.types.Panel):
    bl_label = "模具厚度"
    bl_idname = "HUIER_PT_MuJuHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '参数' and context.scene.muJuTypeEnum != 'OP2'

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'zongHouDu', text="总厚度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'jiHuoBianYuanHouDu', text="激活边缘厚度")


class HUIER_PT_BianYuanHouDu(bpy.types.Panel):
    bl_label = "边缘厚度"
    bl_idname = "HUIER_PT_BianYuanHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_parent_id = "HUIER_PT_MuJuHouDu"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '参数' and context.scene.jiHuoBianYuanHouDu == True

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'waiBuHouDu', text="外部厚度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'waiBuQuYuKuanDu', text="外部区域宽度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'zhongJianHouDu', text="中间厚度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shiFouShiYongNeiBu', text="是否使用内部")
        layout.separator()
        col = layout.column(align=True)
        col.active = context.scene.shiFouShiYongNeiBu
        col.prop(context.scene, 'zhongJianQuYuKuanDu', text="中间区域宽度")
        layout.separator()
        col = layout.column(align=True)
        col.active = context.scene.shiFouShiYongNeiBu
        col.prop(context.scene, 'neiBuHouDu', text="内部厚度")


class HUIER_PT_MianBanAndDianZiSheBei(bpy.types.Panel):
    bl_label = "面板和电子设备"
    bl_idname = "HUIER_PT_MianBanAndDianZiSheBei"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '参数' and (context.scene.muJuTypeEnum == 'OP3' or \
                                                    context.scene.muJuTypeEnum == 'OP5' or \
                                                    context.scene.muJuTypeEnum == 'OP6')

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'mianBanTypeEnum', text="面板类型")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'jieShouQiTypeEnum', text="接收器类型")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'jieShouQiKaiGuanTypeEnum', text="接收器开关类型")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'buJianBTypeEenu', text="部件B")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'mianBanPianYi', text="面板偏移")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'xiaFangYangXianPianYi', text="下放样线偏移")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shangSheRuYinZi', text="上舍入因子")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'xiaSheRuYinZi', text="下舍入因子")


class HUIER_PT_ShangBuQieGeMianBan(bpy.types.Panel):
    bl_label = "上部切割面板"
    bl_idname = "HUIER_PT_ShangBuQieGeMianBan"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '参数' and context.scene.muJuTypeEnum != 'OP2'

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shiFouShangBuQieGeMianBan', text="上部切割面板")
        layout.separator()
        col = layout.column(align=True)
        col.active = context.scene.shiFouShangBuQieGeMianBan
        col.prop(context.scene, 'shangBuQieGeMianBanPianYi', text="上部切割面板偏移")


class HUIER_PT_KongQiangMianBan(bpy.types.Panel):
    bl_label = "空腔面板"
    bl_idname = "HUIER_PT_KongQiangMianBan"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '参数' and context.scene.muJuTypeEnum == 'OP1'

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shiFouKongQiangMianBan', text="空腔面板")
        layout.separator()
        col = layout.column(align=True)
        col.active = context.scene.shiFouKongQiangMianBan
        col.prop(context.scene, 'KongQiangMianBanSheRuPianYi', text="空腔面板舍入")
        layout.separator()
        col = layout.column(align=True)
        col.active = context.scene.shiFouKongQiangMianBan
        col.prop(context.scene, 'ShangBuQieGeBanPianYi', text="上部切割板偏移")


class HUIER_PT_YingErMoCanShu(bpy.types.Panel):
    bl_label = "硬耳膜参数"
    bl_idname = "HUIER_PT_YingErMoCanShu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '参数' and context.scene.muJuTypeEnum == 'OP2'

    def draw(self, context):
        layout = self.layout
        # layout.separator()
        # col = layout.column(align=True)
        # col.prop(context.scene, 'gongXingMianBan', text="拱形面板")
        # layout.separator()
        # col = layout.column(align=True)
        # col.prop(context.scene, 'gongKuan', text="拱宽")
        # layout.separator()
        # col = layout.column(align=True)
        # col.prop(context.scene, 'gongGao', text="拱高")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'yingErMoSheRuPianYi', text="舍入偏移")


class HUIER_PT_TongQiKong1(bpy.types.Panel):
    bl_label = "通气孔"
    bl_idname = "HUIER_PT_TongFengKou"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '参数' and (context.scene.muJuTypeEnum == 'OP3' or \
                                                    context.scene.muJuTypeEnum == 'OP5' or \
                                                    context.scene.muJuTypeEnum == 'OP6')

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shiFouTongFengGuan', text="通风管开关")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'tongFengGuanZhiJing', text="直径")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'tongFengGuanHouDu', text="管厚度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'tongFengGuanWaiBuHouDu', text="外部厚度")

class HUIER_PT_MoBanXuanZe(bpy.types.Panel):
    bl_label = "模板"
    bl_idname = "HUIER_PT_MoBanXuanZe"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'HIDE_HEADER'}


    @classmethod
    def poll(cls, context):
        return context.scene.tabEnum == '模板'

    def draw(self, context):
        layout = self.layout
        # 左列目录
        split = layout.split(factor=0.3)
        box1 = split.box()
        box1.label(text = '模板类别')
        box2 = box1.box()
        col = box2.column()
        col.label(text = '用户模板')
        col.label(text = '预定义模板')
        col.prop(context.scene, "showHdu",
            icon="TRIA_DOWN" if context.scene.showHdu else "TRIA_RIGHT",
            icon_only=True, emboss=False,text = 'HDU'
        )
        if context.scene.showHdu:
            # 右列模板
            icons=load_icons()                                                    
            icon=icons.get("icon_reset")
            col = split.column(align = True)
            grid_flow = col.grid_flow(columns=2,align=True)
            grid_flow.scale_y = 5
            grid_flow.prop_tabs_enum(context.scene, 'muJuTypeEnum',icon_only=True)
            
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)   


# 传声孔
class HUIER_PT_ChuanShenKong1(bpy.types.Panel):
    bl_label = "传声孔"
    bl_idname = "HUIER_PT_ChuanShenKong1"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'gaunDaoPinHua', text="管道平滑")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'chuanShenGuanDaoZhiJing', text="管道直径")


class HUIER_PT_ChuanShenKong2(bpy.types.Panel):
    bl_label = "faceplate opening面板开口"
    bl_idname = "HUIER_PT_ChuanShenKong2"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'active', text="active激活")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shapeEnum', text="形状")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'chuanShenKongOffset', text="offset偏移")


# 通气孔
class HUIER_PT_TongQiKong(bpy.types.Panel):
    bl_label = "通气孔"
    bl_idname = "HUIER_PT_TongQiKong"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "collection"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'tongQiGuanDaoZhiJing', text="管道直径")



class HUIER_PT_YuDingYi(bpy.types.Panel):
    bl_label = "预定义模板"
    bl_idname = "HUIER_PT_YUDINGYI"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_parent_id = "HUIER_PT_TongQiKong"
    bl_context = "collection"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'waiBuHouDu', text="外部厚度")
        

# 耳膜附件
class HUIER_PT_ErMoFuJian(bpy.types.Panel):
    bl_label = "耳膜附件"
    bl_idname = "HUIER_PT_ErMoFuJian"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'erMoFuJianTypeEnum', text="handle耳膜附件")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'erMoFuJianOffset', text="offset偏移")


# 编号       字体大小  字体深度     字体风格
class HUIER_PT_Number(bpy.types.Panel):
    bl_label = "编号"
    bl_idname = "HUIER_PT_Number"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "modifier"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'labelText', text="标签名称")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'fontSize', text="字体尺寸")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'deep', text="深度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'styleEnum', text="风格")


# 软耳模厚度
class HUIER_PT_RuanErMoHouDu(bpy.types.Panel):
    bl_label = "软耳模厚度"
    bl_idname = "HUIER_PT_RuanErMoHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "particle"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'ruanErMoHouDu', text="铸造厚度")


# 支撑
class HUIER_PT_ZhiCheng(bpy.types.Panel):
    bl_label = "支撑"
    bl_idname = "HUIER_PT_ZhiCheng"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'zhiChengTypeEnum', text="support支撑")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'zhiChengOffset', text="offset偏移")


# 排气孔
class HUIER_PT_PaiQiKong(bpy.types.Panel):
    bl_label = "排气孔"
    bl_idname = "HUIER_PT_PaiQiKong"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "constraint"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'paiQiKongTypeEnum', text="sprue型号选择")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'paiQiKongOffset', text="offset偏移")


# 后期打磨
class HUIER_PT_HouQiDaMo(bpy.types.Panel):
    bl_label = "后期打磨"
    bl_idname = "HUIER_PT_HouQiDaMo"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "texture"

    def draw(self, context):
        layout = self.layout
        layout.separator()


# 标题栏
class TOPBAR_HT_upper_bar(bpy.types.Header):
    bl_space_type = 'TOPBAR'

    def draw(self, context):
        region = context.region

        if region.alignment == 'RIGHT':
            self.draw_right(context)
        else:
            self.draw_left(context)

    def draw_left(self, context):
        layout = self.layout
        window = context.window
        screen = context.screen

        TOPBAR_MT_editor_menus.draw_collapsible(
            context, layout)  # File Edit  惠尔文件菜单

        # icons=load_icons()                                                    #标题栏自制图标
        # icon=icons.get("icon_reset")
        # layout.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_backup")
        # layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_forward")
        # layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_grid")
        # layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_ruler")
        # layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_transparency1")
        # layout.menu("TOPBAR_MT_transparency1", text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_transparency2")
        # layout.menu("TOPBAR_MT_transparency2", text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_transparency3")
        # layout.menu("TOPBAR_MT_transparency3", text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_save")
        # layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        # icon = icons.get("icon_viewShift")
        # layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)

    def draw_right(self, context):
        pass

# ********** 标题栏自定义菜单透明度 **********
class TOPBAR_PT_transparency1(bpy.types.Panel):
    bl_label = "透明度1"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        enum = context.scene.transparent1Enum
        col = layout.column()
        col.prop(context.scene, "transparent1Enum", expand=True)
        if enum == 'OP3':
            col.label(text='透明比例')
            row = col.row(align=True)
            row.prop(context.scene, "transparentper1Enum", expand=True)

# 透明度2
class TOPBAR_PT_transparency2(bpy.types.Panel):
    bl_label = "透明度2"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        enum = context.scene.transparent2Enum
        col = layout.column()
        col.prop(context.scene, "transparent2Enum", expand=True)
        if enum == 'OP3':
            col.label(text='透明比例')
            row = col.row(align=True)
            row.prop(context.scene, "transparentper2Enum", expand=True)


# 透明度3
class TOPBAR_PT_transparency3(bpy.types.Panel):
    bl_label = "透明度3"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        enum = context.scene.transparent3Enum
        col = layout.column()
        col.prop(context.scene, "transparent3Enum", expand=True)
        if enum == 'OP3':
            col.label(text='透明比例')
            row = col.row(align=True)
            row.prop(context.scene, "transparentper3Enum", expand=True)


# 第一行的菜单项
class TOPBAR_MT_editor_menus(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        layout.menu("TOPBAR_MT_huierFile")
        layout.menu("TOPBAR_MT_huierView")
        # layout.menu("TOPBAR_MT_file")
        # layout.menu("TOPBAR_MT_edit")
        # layout.menu("TOPBAR_MT_screteEarFile")                             #惠耳文件菜单


# 惠尔文件菜单
class TOPBAR_MT_screteEarFile(bpy.types.Menu):
    bl_label = "文件(惠耳)"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_AREA'
        layout.menu("TOPBAR_MT_file_new", text="新建", icon='FILE_NEW')
        layout.operator("wm.open_mainfile", text="打开...", icon='FILE_FOLDER')

        layout.separator()

        layout.operator_context = 'EXEC_AREA' if context.blend_data.is_saved else 'INVOKE_AREA'
        layout.operator("wm.save_mainfile", text="保存", icon='FILE_TICK')

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_as_mainfile", text="另存为...")
        layout.operator_context = 'INVOKE_AREA'

        layout.separator()

        # layout.menu("TOPBAR_MT_file_import", icon='IMPORT')
        layout.menu("TOPBAR_MT_file_export",text="导出为",icon='EXPORT')
        layout.operator("wm.save_as_mainfile", text="另存为模板")




class Huier_OT_NewFile(bpy.types.Operator):
    bl_idname = "huier.new_file"
    bl_label = "新建"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse_x = 0;
    first_mouse_y = 0;

    def invoke(self,context,event):
        self.first_mouse_x = event.mouse_x;
        self.first_mouse_y = event.mouse_y;
        print('x',self.first_mouse_x)
        print('y',self.first_mouse_y)
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        #移动光标到屏幕中心
        context.window.cursor_warp(context.window.width//2, (context.window.height//2) + 60);
        bpy.ops.screen.userpref_show(section='SAVE_LOAD')
        # context.window.cursor_warp(self.first_mouse_x, self.first_mouse_y);
        return {'FINISHED'}
    
class Huier_OT_addon(bpy.types.Operator):
    bl_idname = "huier.addons"
    bl_label = "查看插件"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.screen.userpref_show(section='ADDONS')
        return {'FINISHED'}

class Huier_OT_keymap(bpy.types.Operator):
    bl_idname = "huier.keymap"
    bl_label = "查看键位映射"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.screen.userpref_show(section='KEYMAP')
        return {'FINISHED'}

class Huier_OT_DaoChuWei(bpy.types.Operator):
    bl_idname = "huier.export"
    bl_label = "导出为"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #移动光标到屏幕中心
        context.window.cursor_warp(context.window.width//2, (context.window.height//2) + 60);
        bpy.ops.screen.userpref_show(section='SYSTEM')
        # bpy.ops.screen.userpref_show()
        # area = bpy.context.window_manager.windows[-1].screen.areas[0]
        # area.type = "FILE_BROWSER"
        # area.ui_type = 'ASSETS'
        return {'FINISHED'}

class Huier_OT_SaveAsMoban(bpy.types.Operator):
    bl_idname = "huier.save_as_moban"
    bl_label = "另存为模板"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #移动光标到屏幕中心
        context.window.cursor_warp(context.window.width//2, (context.window.height//2) + 60);
        bpy.ops.screen.userpref_show(section='FILE_PATHS')
        return {'FINISHED'}

# 自定义的新增菜单
class TOPBAR_MT_huierFile(bpy.types.Menu):
    bl_label = "文件"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_AREA'
        layout.operator("huier.new_file", text="新建", icon='FILE_NEW')
        # layout.operator("wm.open_mainfile", text="打开...", icon='FILE_FOLDER')

        # layout.operator_context = 'EXEC_AREA' if context.blend_data.is_saved else 'INVOKE_AREA'
        # layout.operator("wm.save_mainfile", text="保存", icon='FILE_TICK')

        # layout.operator_context = 'INVOKE_AREA'
        # layout.operator("wm.save_as_mainfile", text="另存为")
        layout.operator_context = 'INVOKE_AREA'

        layout.operator("huier.export",text="导出为",icon='EXPORT')
        layout.operator("huier.save_as_moban", text="另存为模板")

# 原始File菜单
class TOPBAR_MT_file(bpy.types.Menu):
    bl_label = "File"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_AREA'
        layout.menu("TOPBAR_MT_file_new", text="New", icon='FILE_NEW')
        layout.operator("wm.open_mainfile", text="Open...", icon='FILE_FOLDER')
        layout.menu("TOPBAR_MT_file_open_recent")
        layout.operator("wm.revert_mainfile")
        layout.menu("TOPBAR_MT_file_recover")

        layout.separator()

        layout.operator_context = 'EXEC_AREA' if context.blend_data.is_saved else 'INVOKE_AREA'
        layout.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_as_mainfile", text="Save As...")
        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_as_mainfile", text="Save Copy...").copy = True

        layout.separator()

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.link", text="Link...", icon='LINK_BLEND')
        layout.operator("wm.append", text="Append...", icon='APPEND_BLEND')
        layout.menu("TOPBAR_MT_file_previews")

        layout.separator()

        layout.menu("TOPBAR_MT_file_import", icon='IMPORT')
        layout.menu("TOPBAR_MT_file_export", icon='EXPORT')

        layout.separator()

        layout.menu("TOPBAR_MT_file_external_data")
        layout.menu("TOPBAR_MT_file_cleanup")

        layout.separator()

        layout.menu("TOPBAR_MT_file_defaults")

        layout.separator()

        layout.operator("wm.quit_blender", text="Quit", icon='QUIT')


class TOPBAR_MT_edit(bpy.types.Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        show_developer = context.preferences.view.show_developer_ui

        layout.operator("ed.undo")
        layout.operator("ed.redo")

        layout.separator()

        layout.menu("TOPBAR_MT_undo_history")

        layout.separator()

        layout.operator("screen.repeat_last")
        layout.operator("screen.repeat_history", text="Repeat History...")

        layout.separator()

        layout.operator("screen.redo_last", text="Adjust Last Operation...")

        layout.separator()

        layout.operator("wm.search_menu",
                        text="Menu Search...", icon='VIEWZOOM')
        if show_developer:
            layout.operator("wm.search_operator",
                            text="Operator Search...", icon='VIEWZOOM')

        layout.separator()

        # Mainly to expose shortcut since this depends on the context.
        props = layout.operator("wm.call_panel", text="Rename Active Item...")
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        layout.operator("wm.batch_rename", text="Batch Rename...")

        layout.separator()

        # Should move elsewhere (impacts outliner & 3D view).
        tool_settings = context.tool_settings
        layout.prop(tool_settings, "lock_object_mode")

        layout.separator()

        layout.operator("screen.userpref_show",
                        text="Preferences...", icon='PREFERENCES')

# 视图菜单
class TOPBAR_MT_huierView(bpy.types.Menu):
    bl_label = "视图"

    def draw(self, context):
        global show_prop
        layout = self.layout
        if show_prop:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'
        layout.operator_context = 'INVOKE_AREA'
        layout.operator("screen.toggleproperty", text="属性栏", icon=icon)


# ********** 3D视图下的菜单栏 **********

# 监听响应
def test():
    global left_last_dis,right_last_dis,left_last_rot,right_last_rot,left_last_loc,right_last_loc
    override1 = getOverride()
    override2 = getOverride2()
    area1 = override1['area']
    area2 = override2['area']
    rv3d1 = area1.spaces.active.region_3d
    rv3d2 = area2.spaces.active.region_3d
    view_dis1 = rv3d1.view_distance
    view_dis2 = rv3d2.view_distance
    view_rot1 = rv3d1.view_rotation
    view_rot2 = rv3d2.view_rotation
    view_loc1 = rv3d1.view_location
    view_loc2 = rv3d2.view_location
    if bpy.context.window.workspace.name == '布局.001':
        # 视角缩放
        if view_dis1 != left_last_dis:
            print('view_dis1',view_dis1)
            area2.spaces.active.region_3d.view_distance = view_dis1
            print('area2',area2.spaces.active.region_3d.view_distance)
            print('area1',area1.spaces.active.region_3d.view_distance)
            left_last_dis = view_dis1
            return
        elif view_dis2 != right_last_dis:
            print('view_dis2',view_dis1)
            area2.spaces.active.region_3d.view_distance = view_dis1
            print('area2',area2.spaces.active.region_3d.view_distance)
            print('area1',area1.spaces.active.region_3d.view_distance)
            right_last_dis = view_dis2
            return
        
        if view_loc1 != left_last_loc:
            new = mathutils.Vector((view_loc1[0],-view_loc1[1],view_loc1[2]))
            area2.spaces.active.region_3d.view_location = new 
            # return
        
        # 视角旋转
        if view_rot1 != left_last_rot:
            # print('view1',view_rot1)
            # print('view2',view_rot2)
            quat_a = mathutils.Quaternion((view_rot1[3], view_rot1[2], view_rot1[1], view_rot1[0]))
            area2.spaces.active.region_3d.view_rotation = quat_a
            # left_last_rot = view_rot1
            return
        elif view_rot2 != right_last_rot:
            quat_a = mathutils.Quaternion((view_rot2[3], view_rot2[2], view_rot2[1], view_rot2[0]))
            area1.spaces.active.region_3d.view_rotation = quat_a
            # right_last_rot = view_rot2
            return


def notify_test(context):
    global prev_context
    override = []
    is_initial = True
    if (context.window.workspace.name == '布局.001'):
        # 切换到之前窗口的模式
        bpy.context.screen.areas[1].spaces.active.context = 'RENDER'
        workspace = context.window.workspace
        for screen in workspace.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    # 这里我们无法获取窗口和workspace的引用
                    ride = {'screen': screen, 'area': area}
                    override.append(ride)

                    if (area.spaces.active.use_local_collections == False):
                        # 设置local collection
                        is_initial = False
                        area.spaces.active.use_local_collections = True

        if not is_initial:
            # 初始化，设定活动集合为右耳
            with bpy.context.temp_override(**override[0]):
                bpy.ops.object.hide_collection(collection_index=1, extend=False)
            with bpy.context.temp_override(**override[1]):
                bpy.ops.object.hide_collection(collection_index=2, extend=False)

        # 当前活动集合与活动物体不匹配
        if bpy.context.scene.activecollecionMirror != bpy.context.scene.leftWindowObj:
            with bpy.context.temp_override(**override[0]):
                bpy.ops.object.hide_collection(collection_index=1, extend=False, toggle=True)
                bpy.ops.object.hide_collection(collection_index=2, extend=False, toggle=True)
            with bpy.context.temp_override(**override[1]):
                bpy.ops.object.hide_collection(collection_index=1, extend=False, toggle=True)
                bpy.ops.object.hide_collection(collection_index=2, extend=False, toggle=True)
            bpy.context.scene.activecollecionMirror = bpy.context.scene.leftWindowObj

    else:
        # 切换到之前窗口的模式
        bpy.context.screen.areas[1].spaces.active.context = 'RENDER'

        workspace = context.window.workspace
        for screen in workspace.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    # 这里我们无法获取窗口和workspace的引用
                    ride = {'screen': screen, 'area': area}
                    override.append(ride)

        # 当前活动集合与活动物体不匹配
        if bpy.context.scene.activecollecion != bpy.context.scene.leftWindowObj:
            with bpy.context.temp_override(**override[0]):
                bpy.ops.object.hide_collection(collection_index=1, extend=False, toggle=True)
                bpy.ops.object.hide_collection(collection_index=2, extend=False, toggle=True)
            with bpy.context.temp_override(**override[1]):
                bpy.ops.object.hide_collection(collection_index=1, extend=False, toggle=True)
                bpy.ops.object.hide_collection(collection_index=2, extend=False, toggle=True)
            bpy.context.scene.activecollecion = bpy.context.scene.leftWindowObj

    # 切换布局时重绘右上角标识
    draw_font()

# 给3d区域添加监听器
SpaceView3D.my_handler = SpaceView3D.draw_handler_add(test, (), 'WINDOW', 'PRE_VIEW')


# 切换左右耳窗口
class Huier_OT_SwitchWorkspace(bpy.types.Operator):
    bl_idname = "huier.switch"
    bl_label = "切换窗口"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global prev_context

        # 监听workspace切换到左右耳窗口
        subscribe_to = bpy.types.Window,'workspace'
        bpy.msgbus.subscribe_rna(
            key=subscribe_to,
            owner=object(),
            args=(bpy.context,),
            notify=notify_test,
        )
        bpy.msgbus.publish_rna(key=subscribe_to)

        # MyHandleClass.add_handler(
        #                             draw_right, (None,'R'))
        # MyHandleClass.add_handler(
        #                             draw_left, (None,'L'))

        if bpy.context.window.workspace.name == '布局':
            # 保存之前窗口的模式
            prev_context = bpy.context.screen.areas[1].spaces.active.context
            bpy.context.window.workspace = bpy.data.workspaces['布局.001']
            # 获取"MyCollection"的LayerCollection对象
            my_layer_collection = get_layer_collection(bpy.context.view_layer.layer_collection, 'Right')
            # 将"MyCollection"设置为活动层集合
            if my_layer_collection:
                bpy.context.view_layer.active_layer_collection = my_layer_collection
        
            
        if bpy.context.window.workspace.name == '布局.001':
            # 保存之前窗口的模式
            prev_context = bpy.context.screen.areas[1].spaces.active.context
            bpy.context.window.workspace = bpy.data.workspaces['布局']


        return {'FINISHED'}



class VIEW3D_HT_header(bpy.types.Header):
    bl_space_type = 'VIEW_3D'

    def draw(self,context):
        layout = self.layout
        icons=load_icons()                                                    #标题栏自制图标

        icon = icons.get("icon_backup")
        layout.operator("obj.undo1", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_forward")
        layout.operator("obj.redo1", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_grid")
        layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_ruler")
        layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_viewShift")
        layout.operator("huier.switch", text="", icon_value=icon.icon_id)

        row = layout.row(align=True)
        icon = icons.get("icon_transparency1")
        row.prop(context.scene, "transparent1", text="", icon_value=icon.icon_id, icon_only=True)
        sub = row.row(align=True)
        sub.popover("TOPBAR_PT_transparency1", text="")

        row = layout.row(align=True)
        icon = icons.get("icon_transparency2")
        row.prop(context.scene, "transparent2", text="", icon_value=icon.icon_id, icon_only=True)
        sub = row.row(align=True)
        sub.popover("TOPBAR_PT_transparency2", text="")

        row = layout.row(align=True)
        icon = icons.get("icon_transparency3")
        row.prop(context.scene, "transparent3", text="", icon_value=icon.icon_id, icon_only=True)
        sub = row.row(align=True)
        sub.popover("TOPBAR_PT_transparency3", text="")


# 测试按钮功能
class HUIER_PT_TestButton(bpy.types.Panel):
    bl_label = "按钮测试"
    bl_idname = "HUIER_PT_Button"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TestButton"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("obj.initialcolor", text="初始化模型颜色")
        col.operator("obj.initialtransparency", text="透明")
        # col.operator("obj.localthickeningreset", text="重置")
        # col.operator("obj.localthickeningaddarea", text="扩大区域")
        # col.operator("obj.localthickeningreducearea", text="缩小区域")
        # col.operator("obj.localthickeningthick", text="加厚")
        # col.operator("obj.localthickeningsubmit", text="提交")
        # col.operator("object.smooth", text="光滑")
        # col.operator("obj.undo", text="撤销")
        # col.operator("obj.redo", text="重做")
        # col.operator("object.switchtestfunc", text="磨具功能测试")
        col.operator("obj.localthickeningjingxiang", text="加厚镜像")

class ToggleProperty(bpy.types.Operator):
    bl_idname = "screen.toggleproperty"
    bl_label = "显示隐藏属性栏"

    __initial_mouse_x = None  
    __initial_mouse_y = None

    def invoke(self, context, event):
        # 记录点击位置
        self.__initial_mouse_x = event.mouse_x
        self.__initial_mouse_y = event.mouse_y
        self.execute(context)
        return {'FINISHED'}


    def execute(self, context):
        global show_prop

        workspace = bpy.context.window.workspace.name
        if workspace == '布局.001':
            context = bpy.context
            initx = self.__initial_mouse_x
            inity = self.__initial_mouse_y
            w = context.window
            area = bpy.context.screen.areas[0]
            if area.height > 50:
                show_prop = True
            else:
                show_prop = False
            x = area.x+int(area.width/2)
            y = area.y+area.height+3
            w.cursor_warp(x, y)
            if show_prop == False:
                delta= 300 - area.height
                show_prop = True
            else:
                delta = -area.height+1
                show_prop = False
            bpy.app.timers.register(functools.partial(snooper, context.copy(), w,initx, inity, x, y, delta=delta), first_interval=0.2)

        return {'FINISHED'}

def snooper(c,w, initx, inity, x, y, delta):
    global show_prop
    poll_retries  = 100
    while not bpy.ops.screen.area_move.poll():
        # show_prop = not show_prop
        poll_retries -= 1
        if not poll_retries:
            return None # out of retries

    # 移动边界
    bpy.ops.screen.area_move(x=x, y=y,delta =delta)

    # 光标移动回按钮点击位置
    w.cursor_warp(initx, inity)
    return None

# 注册类
_classes = [
    # VIEW3D_HT_header,
    HUIER_PT_damo_R,
    HUIER_PT_damo_L,
    HUIER_PT_LocalOrGlobalJiaHou,
    # HUIER_PT_LocalOrGlobalJiaHou2,
    HUIER_PT_DianMianQieGe,
    HUIER_PT_PlantCut,
    HUIER_PT_StepCut,
    HUIER_PT_ChuangJianMuJu,
    HUIER_PT_MuJuHouDu,
    HUIER_PT_MuJuPianYi,
    HUIER_PT_BianYuanHouDu,
    HUIER_PT_MianBanAndDianZiSheBei,
    HUIER_PT_ShangBuQieGeMianBan,
    HUIER_PT_KongQiangMianBan,
    HUIER_PT_YingErMoCanShu,
    HUIER_PT_TongQiKong1,
    HUIER_PT_ChuanShenKong1,
    # HUIER_PT_ChuanShenKong2,
    HUIER_PT_TongQiKong,
    HUIER_PT_ErMoFuJian,
    HUIER_PT_Number,
    HUIER_PT_RuanErMoHouDu,
    HUIER_PT_ZhiCheng,
    HUIER_PT_PaiQiKong,
    HUIER_PT_HouQiDaMo,
    # TOPBAR_HT_upper_bar,
    TOPBAR_PT_transparency1,
    TOPBAR_PT_transparency2,
    TOPBAR_PT_transparency3,
    # TOPBAR_MT_editor_menus,
    TOPBAR_MT_screteEarFile,
    TOPBAR_MT_huierFile,
    TOPBAR_MT_huierView,
    # TOPBAR_MT_file,
    # TOPBAR_MT_edit,
    # HUIER_PT_TestButton,
    Huier_OT_addon,
    Huier_OT_keymap,
    Huier_OT_NewFile,
    Huier_OT_DaoChuWei,
    Huier_OT_SaveAsMoban,
    HUIER_PT_MoJuTab,
    HUIER_PT_MoBanXuanZe,
    Huier_OT_SwitchWorkspace,
    ToggleProperty
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
