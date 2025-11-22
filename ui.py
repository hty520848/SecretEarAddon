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
import bpy_extras
from bpy_extras.io_utils import ImportHelper
from .icon.icons import load_icons
from .icon.icons import clear_icons
from bpy.props import BoolProperty
from .tool import getOverride, getOverride2, get_layer_collection
import mathutils
import bmesh
from bpy_extras import view3d_utils
from bpy.types import SpaceView3D
import math
import time, functools
from .public_operation import processing_stage_dict, order_processing_list, set_prev_context, fallback
from .sound_canal import get_is_on_rotate
from .create_tip.cut_mould import get_color_mode
from .parameter import set_switch_flag, get_switch_flag, get_mirror_context, set_mirror_context, check_modals_running
from .pymesh.pymesh import register_globals, write_to_pickle, import_sed_file
from .global_manager import global_manager
import subprocess

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

# 不同布局间的监听是否启动
is_listen_start = False


def register_ui_globals():
    global prev_context
    global show_prop
    global_manager.register("prev_context", prev_context)
    global_manager.register("show_prop", show_prop)


# 打磨面板
class HUIER_PT_damo(bpy.types.Panel):
    bl_label = "耳样处理"
    bl_idname = "HUIER_PT_damo_R"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    # @classmethod
    # def poll(cls, context):
    #     return context.scene.leftWindowObj == '右耳'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.separator()
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            col.prop(context.scene, 'laHouDUR', text="蜡厚度")
            col.separator()
            col.prop(context.scene, 'damo_scale_strength_R', text="打磨强度")
            col.separator()
            col.prop(context.scene, 'localLaHouDuR', text="局部蜡厚度限制")
            col = layout.column()
            col.active = context.scene.localLaHouDuR
            col.prop(context.scene, 'maxLaHouDuR', text="最大蜡厚度")
            col.separator()
            col.prop(context.scene, 'minLaHouDuR', text="最小蜡厚度")
        else:
            col.prop(context.scene, 'laHouDUL', text="蜡厚度")
            col.separator()
            col.prop(context.scene, 'damo_scale_strength_L', text="打磨强度")
            col.separator()
            col.prop(context.scene, 'localLaHouDuL', text="局部蜡厚度限制")
            col = layout.column()
            col.active = context.scene.localLaHouDuL
            col.prop(context.scene, 'maxLaHouDuL', text="最大蜡厚度")
            col.separator()
            col.prop(context.scene, 'minLaHouDuL', text="最小蜡厚度")


# 局部或整体加厚面板
class HUIER_PT_LocalOrGlobalJiaHou(bpy.types.Panel):
    bl_label = "局部或整体加厚"
    bl_idname = "HUIER_PT_LocalOrGlobalJiaHou"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "output"

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            col.prop(context.scene, 'localThicking_offset', text="偏移值")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'localThicking_borderWidth', text="边框宽度")
        else:
            col.prop(context.scene, 'localThicking_offset_L', text="偏移值")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'localThicking_borderWidth_L', text="边框宽度")


# 点面切割
class HUIER_PT_DianMianQieGe(bpy.types.Panel):
    bl_label = "选择工具"
    bl_idname = "HUIER_PT_DianMianQieGe"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        if context.scene.leftWindowObj == '右耳':
            col.prop(context.scene, 'qieGeTypeEnumR', text="选择工具")
        else:
            col.prop(context.scene, 'qieGeTypeEnumL', text="选择工具")


class HUIER_PT_PlantCut(bpy.types.Panel):
    bl_label = "plant cut平面切割"
    bl_idname = "HUIER_PT_PlantCut"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"

    @classmethod
    def poll(cls, context):
        return (not context.scene.pressfinish and
                ((context.scene.qieGeTypeEnumR == 'OP1' and context.scene.leftWindowObj == '右耳') or
                 (context.scene.qieGeTypeEnumL == 'OP1' and context.scene.leftWindowObj == '左耳')))

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        if context.scene.leftWindowObj == '右耳':
            col.prop(context.scene, 'qiegesheRuPianYiR', text="舍入偏移")
        else:
            col.prop(context.scene, 'qiegesheRuPianYiL', text="舍入偏移")
        layout.separator()


class HUIER_PT_StepCut(bpy.types.Panel):
    bl_label = "step vent阶梯状切割"
    bl_idname = "HUIER_PT_StepCut"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"

    @classmethod
    def poll(cls, context):
        return (not context.scene.pressfinish and
                ((context.scene.qieGeTypeEnumR == 'OP2' and context.scene.leftWindowObj == '右耳') or
                 (context.scene.qieGeTypeEnumL == 'OP2' and context.scene.leftWindowObj == '左耳')))

    def draw(self, context):
        layout = self.layout
        layout.separator()
        # layout.active = (context.scene.qieGeTypeEnum == 'OP2')
        col = layout.column(align=True)
        if context.scene.leftWindowObj == '右耳':
            col.prop(context.scene, 'qiegewaiBianYuanR', text="外边缘平滑偏移")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'qiegeneiBianYuanR', text="内边缘平滑偏移")
        else:
            col.prop(context.scene, 'qiegewaiBianYuanL', text="外边缘平滑偏移")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'qiegeneiBianYuanL', text="内边缘平滑偏移")


class HUIER_PT_MoJuTab(bpy.types.Panel):
    bl_label = ""
    bl_idname = "HUIER_PT_MoJuTab"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        col = layout.split(factor=0.4)
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
        return not context.scene.pressfinish and context.scene.tabEnum == '参数'

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
        return (not context.scene.pressfinish and context.scene.tabEnum == '参数' and
                (context.scene.muJuTypeEnum != 'OP2' and context.scene.muJuTypeEnum != 'OP3'))

    def draw(self, context):
        layout = self.layout
        if context.scene.leftWindowObj == '右耳':
            col = layout.column(align=True)
            col.prop(context.scene, 'neiBianJiXianR', text="内编辑线")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'waiBianYuanSheRuPianYiR', text="外舍入偏移")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'neiBianYuanSheRuPianYiR', text="内舍入偏移")
        else:
            col = layout.column(align=True)
            col.prop(context.scene, 'neiBianJiXianL', text="内编辑线")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'waiBianYuanSheRuPianYiL', text="外舍入偏移")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'neiBianYuanSheRuPianYiL', text="内舍入偏移")


class HUIER_PT_MuJuHouDu(bpy.types.Panel):
    bl_label = "模具厚度"
    bl_idname = "HUIER_PT_MuJuHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (not context.scene.pressfinish and context.scene.tabEnum == '参数' and 
                (context.scene.muJuTypeEnum == 'OP1' or context.scene.muJuTypeEnum == 'OP3' or
                 context.scene.muJuTypeEnum == 'OP4' or context.scene.muJuTypeEnum == 'OP5'))

    def draw(self, context):
        layout = self.layout
        if context.scene.leftWindowObj == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.active = not context.scene.jiHuoBianYuanHouDuR
            col.prop(context.scene, 'zongHouDuR', text="总厚度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'jiHuoBianYuanHouDuR', text="激活边缘厚度")
        else:
            layout.separator()
            col = layout.column(align=True)
            col.active = not context.scene.jiHuoBianYuanHouDuL
            col.prop(context.scene, 'zongHouDuL', text="总厚度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'jiHuoBianYuanHouDuL', text="激活边缘厚度")


class HUIER_PT_BianYuanHouDu(bpy.types.Panel):
    bl_label = "边缘厚度"
    bl_idname = "HUIER_PT_BianYuanHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_parent_id = "HUIER_PT_MuJuHouDu"

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.scene.leftWindowObj == '右耳':
            return not context.scene.pressfinish and context.scene.tabEnum == '参数' and context.scene.jiHuoBianYuanHouDuR
        else:
            return not context.scene.pressfinish and context.scene.tabEnum == '参数' and context.scene.jiHuoBianYuanHouDuL

    def draw(self, context):
        layout = self.layout
        if context.scene.leftWindowObj == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'waiBuHouDuR', text="外部厚度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'waiBuQuYuKuanDuR', text="外部区域宽度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'zhongJianHouDuR', text="中间厚度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'shiFouShiYongNeiBuR', text="是否使用内部")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.shiFouShiYongNeiBuR
            col.prop(context.scene, 'zhongJianQuYuKuanDuR', text="中间区域宽度")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.shiFouShiYongNeiBuR
            col.prop(context.scene, 'neiBuHouDuR', text="内部厚度")
        else:
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'waiBuHouDuL', text="外部厚度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'waiBuQuYuKuanDuL', text="外部区域宽度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'zhongJianHouDuL', text="中间厚度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'shiFouShiYongNeiBuL', text="是否使用内部")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.shiFouShiYongNeiBuL
            col.prop(context.scene, 'zhongJianQuYuKuanDuL', text="中间区域宽度")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.shiFouShiYongNeiBuL
            col.prop(context.scene, 'neiBuHouDuL', text="内部厚度")


class HUIER_PT_MianBanAndDianZiSheBei(bpy.types.Panel):
    bl_label = "面板和电子设备"
    bl_idname = "HUIER_PT_MianBanAndDianZiSheBei"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (not context.scene.pressfinish and context.scene.tabEnum == '参数' and
                (context.scene.muJuTypeEnum == 'OP3' or context.scene.muJuTypeEnum == 'OP5' or
                 context.scene.muJuTypeEnum == 'OP6'))

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
        col.prop(context.scene, 'jieShouQiKaiGuanTypeEnum', text="开关类型")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'buJianBTypeEnum', text="部件B")

        if context.scene.leftWindowObj == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'mianBanPianYiR', text="面板偏移")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'xiaFangYangXianPianYiR', text="下放样线偏移")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'shangSheRuYinZiR', text="上舍入因子")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'xiaSheRuYinZiR', text="下舍入因子")

        else:
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'mianBanPianYiL', text="面板偏移")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'xiaFangYangXianPianYiL', text="下放样线偏移")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'shangSheRuYinZiL', text="上舍入因子")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'xiaSheRuYinZiL', text="下舍入因子")


class HUIER_PT_ShangBuQieGeMianBan(bpy.types.Panel):
    bl_label = "上部切割面板"
    bl_idname = "HUIER_PT_ShangBuQieGeMianBan"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish and context.scene.tabEnum == '参数' and context.scene.muJuTypeEnum != 'OP2'

    def draw(self, context):
        layout = self.layout
        if context.scene.leftWindowObj == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'shiFouShangBuQieGeMianBanR', text="上部切割面板")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.shiFouShangBuQieGeMianBanR
            col.prop(context.scene, 'shangBuQieGeMianBanPianYiR', text="上部切割面板舍入")
        else:
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'shiFouShangBuQieGeMianBanL', text="上部切割面板")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.shiFouShangBuQieGeMianBanL
            col.prop(context.scene, 'shangBuQieGeMianBanPianYiL', text="上部切割面板偏移舍入")


class HUIER_PT_KongQiangMianBan(bpy.types.Panel):
    bl_label = "空腔面板"
    bl_idname = "HUIER_PT_KongQiangMianBan"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (not context.scene.pressfinish and context.scene.tabEnum == '参数' and
                (context.scene.muJuTypeEnum == 'OP1' or context.scene.muJuTypeEnum == 'OP4' or
                 context.scene.muJuTypeEnum == 'OP3' or context.scene.muJuTypeEnum == 'OP5'))

    def draw(self, context):
        layout = self.layout
        if context.scene.leftWindowObj == '右耳':
            kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumR
            layout.separator()
            col = layout.column(align=True)
            # col.prop(context.scene, 'shiFouKongQiangMianBanR', text="空腔面板")
            col.prop(context.scene, 'KongQiangMianBanTypeEnumR', text="空腔面板")
            if(kongQiangMianBanType != 'OP3'):
                layout.separator()
                col = layout.column(align=True)
                col.active = (context.scene.KongQiangMianBanTypeEnumR == 'OP1' or context.scene.KongQiangMianBanTypeEnumR == 'OP2')
                col.prop(context.scene, 'KongQiangMianBanSheRuPianYiR', text="空腔面板舍入")
            if(kongQiangMianBanType == 'OP2'):
                layout.separator()
                col = layout.column(align=True)
                col.active = (context.scene.KongQiangMianBanTypeEnumR == 'OP2')
                col.prop(context.scene, 'ShangBuQieGeBanPianYiR', text="上部切割面板偏移")
        else:
            kongQiangMianBanType = bpy.context.scene.KongQiangMianBanTypeEnumL
            layout.separator()
            col = layout.column(align=True)
            # col.prop(context.scene, 'shiFouKongQiangMianBanL', text="空腔面板")
            col.prop(context.scene, 'KongQiangMianBanTypeEnumL', text="空腔面板")
            if (kongQiangMianBanType != 'OP3'):
                layout.separator()
                col = layout.column(align=True)
                col.active = (context.scene.KongQiangMianBanTypeEnumL == 'OP1' or context.scene.KongQiangMianBanTypeEnumL == 'OP2')
                col.prop(context.scene, 'KongQiangMianBanSheRuPianYiL', text="空腔面板舍入")
            if (kongQiangMianBanType == 'OP2'):
                layout.separator()
                col = layout.column(align=True)
                col.active = (context.scene.KongQiangMianBanTypeEnumL == 'OP2')
                col.prop(context.scene, 'ShangBuQieGeBanPianYiL', text="上部切割面板偏移")


class HUIER_PT_YingErMoCanShu(bpy.types.Panel):
    bl_label = "硬耳膜参数"
    bl_idname = "HUIER_PT_YingErMoCanShu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish and context.scene.tabEnum == '参数' and context.scene.muJuTypeEnum == 'OP2'

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
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            col.prop(context.scene, 'yingErMoSheRuPianYiR', text="舍入偏移")
        else:
            col.prop(context.scene, 'yingErMoSheRuPianYiL', text="舍入偏移")


class HUIER_PT_TongQiKong1(bpy.types.Panel):
    bl_label = "通气孔"
    bl_idname = "HUIER_PT_TongFengKou"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (not context.scene.pressfinish and context.scene.tabEnum == '参数' and
                (context.scene.muJuTypeEnum == 'OP3' or context.scene.muJuTypeEnum == 'OP5' or
                 context.scene.muJuTypeEnum == 'OP6'))

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'useShellCanalR', text="开启通风管")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalR
            col.prop(context.scene, 'shellCanalDiameterR', text="通风管道直径")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalR
            col.prop(context.scene, 'shellCanalThicknessR', text="通风管道厚度")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalR
            col.prop(context.scene, 'shellCanalOffsetR', text="通风管道偏移")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalR
            col.prop(context.scene, 'innerShellCanalOffsetR', text="通风管道内部平滑")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalR
            col.prop(context.scene, 'outerShellCanalOffsetR', text="通风管道外部平滑")
        else:
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'useShellCanalL', text="开启通风管")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalL
            col.prop(context.scene, 'shellCanalDiameterL', text="通风管道直径")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalL
            col.prop(context.scene, 'shellCanalThicknessL', text="通风管道厚度")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalL
            col.prop(context.scene, 'shellCanalOffsetL', text="通风管道偏移")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalL
            col.prop(context.scene, 'innerShellCanalOffsetL', text="通风管道内部平滑")
            layout.separator()
            col = layout.column(align=True)
            col.active = context.scene.useShellCanalL
            col.prop(context.scene, 'outerShellCanalOffsetL', text="通风管道外部平滑")


class HUIER_PT_MoBanXuanZe(bpy.types.Panel):
    bl_label = "模板"
    bl_idname = "HUIER_PT_MoBanXuanZe"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish and context.scene.tabEnum == '模板'

    def draw(self, context):
        layout = self.layout
        # 左列目录
        split = layout.split(factor=0.3)
        box1 = split.box()
        box1.label(text='模板类别')
        box2 = box1.box()
        col = box2.column()
        col.label(text='用户模板')
        col.label(text='预定义模板')
        scene = context.scene
        # 获取所有以 "use_template_" 开头的变量
        template_props = [
            prop for prop in dir(scene)
            if prop.startswith("use_template_")
        ]

        for prop in template_props:
            selected_template = getattr(bpy.context.scene, prop)
            template_name = prop.replace("use_template_", "")
            col.prop(context.scene, prop,
                     icon="TRIA_DOWN" if selected_template else "TRIA_RIGHT",
                     icon_only=True, emboss=False, text=template_name
                     )
        for prop in template_props:
            selected_template = getattr(bpy.context.scene, prop)
            if selected_template:
                col = split.column(align=True)
                grid_flow = col.grid_flow(columns=2, align=True)
                grid_flow.scale_y = 5
                template_name = prop.replace("use_template_", "")
                if template_name == "HDU":
                    grid_flow.prop_tabs_enum(context.scene, 'muJuTypeEnum', icon_only=True)
                else:
                    template_enum_name = f"template_{template_name}"
                    template_enum = getattr(context.scene, prop)
                    if template_enum:
                        grid_flow.prop_tabs_enum(context.scene, template_enum_name, icon_only=False)
        # col.prop(context.scene, "showHdu",
        #          icon="TRIA_DOWN" if context.scene.showHdu else "TRIA_RIGHT",
        #          icon_only=True, emboss=False, text='HDU'
        #          )
        # col.prop(context.scene, "showHuier",
        #          icon="TRIA_DOWN" if context.scene.showHuier else "TRIA_RIGHT",
        #          icon_only=True, emboss=False, text='Huier'
        #          )
        # if context.scene.showHdu:
        #     # 右列模板
        #     # icons = load_icons()
        #     # icon = icons.get("icon_reset")
        #     col = split.column(align=True)
        #     grid_flow = col.grid_flow(columns=2, align=True)
        #     grid_flow.scale_y = 5
        #     grid_flow.prop_tabs_enum(context.scene, 'muJuTypeEnum', icon_only=True)

            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
            # grid_flow.operator("wm.open_mainfile",text="", icon_value=icon.icon_id)
        # elif context.scene.showHuier:
        #     # 右列模板
        #     col = split.column(align=True)
        #     grid_flow = col.grid_flow(columns=2, align=True)
        #     grid_flow.scale_y = 5
        #     grid_flow.prop_tabs_enum(context.scene, 'HuierTypeEnum', icon_only=False)



# 传声孔
class HUIER_PT_ChuanShenKong1(bpy.types.Panel):
    bl_label = "传声孔"
    bl_idname = "HUIER_PT_ChuanShenKong1"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        name = bpy.context.scene.leftWindowObj
        shape_enum = bpy.context.scene.soundcancalShapeEnum
        shape_enum_l = bpy.context.scene.soundcancalShapeEnum_L
        if name == '右耳':
            col.prop(context.scene, 'gaunDaoPinHua', text="管道平滑")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'chuanShenGuanDaoZhiJing', text="管道直径")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'soundcancalShapeEnum', text="管道类型")

            if (shape_enum == 'OP2'):
                layout.separator()
                col = layout.column(align=True)
                # col.active = not get_is_on_rotate()
                col.prop(context.scene, 'chuanShenKongOffset', text="管道偏移")
        else:
            col.prop(context.scene, 'gaunDaoPinHua_L', text="管道平滑")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'chuanShenGuanDaoZhiJing_L', text="管道直径")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'soundcancalShapeEnum_L', text="管道类型")
            if (shape_enum_l == 'OP2'):
                layout.separator()
                col = layout.column(align=True)
                # col.active = not get_is_on_rotate()
                col.prop(context.scene, 'chuanShenKongOffset_L', text="管道偏移")


class HUIER_PT_ChuanShenKong2(bpy.types.Panel):
    bl_label = "faceplate opening面板开口"
    bl_idname = "HUIER_PT_ChuanShenKong2"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

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

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            col.prop(context.scene, 'tongQiGuanDaoZhiJing', text="管道直径")
        else:
            col.prop(context.scene, 'tongQiGuanDaoZhiJing_L', text="管道直径")


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

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'erMoFuJianTypeEnum', text="handle耳膜附件")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'erMoFuJianOffset', text="offset偏移")
        elif name == '左耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'erMoFuJianTypeEnumL', text="handle耳膜附件")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'erMoFuJianOffsetL', text="offset偏移")


# 编号       字体大小  字体深度     字体风格
class HUIER_PT_Number(bpy.types.Panel):
    bl_label = "编号"
    bl_idname = "HUIER_PT_Number"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "modifier"

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
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
        elif name == '左耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'labelTextL', text="标签名称")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'fontSizeL', text="字体尺寸")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'deepL', text="深度")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'styleEnumL', text="风格")


# 软耳模厚度
class HUIER_PT_RuanErMoHouDu(bpy.types.Panel):
    bl_label = "软耳模厚度"
    bl_idname = "HUIER_PT_RuanErMoHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "particle"

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'ruanErMoHouDu', text="铸造厚度")
        elif name == '左耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'ruanErMoHouDuL', text="铸造厚度")


# 支撑
class HUIER_PT_ZhiCheng(bpy.types.Panel):
    bl_label = "支撑"
    bl_idname = "HUIER_PT_ZhiCheng"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "physics"

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'zhiChengTypeEnum', text="support支撑")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'zhiChengOffset', text="offset偏移")
        elif name == '左耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'zhiChengTypeEnumL', text="support支撑")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'zhiChengOffsetL', text="offset偏移")


# 排气孔
class HUIER_PT_PaiQiKong(bpy.types.Panel):
    bl_label = "排气孔"
    bl_idname = "HUIER_PT_PaiQiKong"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "constraint"

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'paiQiKongTypeEnum', text="sprue型号选择")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'paiQiKongOffset', text="offset偏移")
        elif name == '左耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'paiQiKongTypeEnumL', text="sprue型号选择")
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'paiQiKongOffsetL', text="offset偏移")


class HUIER_PT_CutMould(bpy.types.Panel):
    bl_label = "模具切割"
    bl_idname = "HUIER_PT_CutMould"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return not context.scene.pressfinish

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'cutmouldpianyiR', text="切割边缘圆滑宽度")
        elif name == '左耳':
            layout.separator()
            col = layout.column(align=True)
            col.prop(context.scene, 'cutmouldpianyiL', text="切割边缘圆滑宽度")


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
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            enum = context.scene.transparent1EnumR
            col = layout.column()
            col.prop(context.scene, "transparent1EnumR", expand=True)
            if enum == 'OP3':
                col.label(text='透明比例')
                row = col.row(align=True)
                row.prop(context.scene, "transparentper1EnumR", expand=True)

        elif name == '左耳':
            enum = context.scene.transparent1EnumL
            col = layout.column()
            col.prop(context.scene, "transparent1EnumL", expand=True)
            if enum == 'OP3':
                col.label(text='透明比例')
                row = col.row(align=True)
                row.prop(context.scene, "transparentper1EnumL", expand=True)


# 透明度2
class TOPBAR_PT_transparency2(bpy.types.Panel):
    bl_label = "透明度2"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            enum = context.scene.transparent2EnumR
            col = layout.column()
            col.prop(context.scene, "transparent2EnumR", expand=True)
            if enum == 'OP3':
                col.label(text='透明比例')
                row = col.row(align=True)
                row.prop(context.scene, "transparentper2EnumR", expand=True)

        elif name == '左耳':
            enum = context.scene.transparent2EnumL
            col = layout.column()
            col.prop(context.scene, "transparent2EnumL", expand=True)
            if enum == 'OP3':
                col.label(text='透明比例')
                row = col.row(align=True)
                row.prop(context.scene, "transparentper2EnumL", expand=True)


# 透明度3
class TOPBAR_PT_transparency3(bpy.types.Panel):
    bl_label = "透明度3"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"

    def draw(self, context):
        layout = self.layout
        name = bpy.context.scene.leftWindowObj
        if name == '右耳':
            enum = context.scene.transparent3EnumR
            col = layout.column()
            col.prop(context.scene, "transparent3EnumR", expand=True)
            if enum == 'OP3':
                col.label(text='透明比例')
                row = col.row(align=True)
                row.prop(context.scene, "transparentper3EnumR", expand=True)

        elif name == '左耳':
            enum = context.scene.transparent3EnumL
            col = layout.column()
            col.prop(context.scene, "transparent3EnumL", expand=True)
            if enum == 'OP3':
                col.label(text='透明比例')
                row = col.row(align=True)
                row.prop(context.scene, "transparentper3EnumL", expand=True)


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


class Huier_OT_NewFile(bpy.types.Operator):
    bl_idname = "huier.new_file"
    bl_label = "新建"
    bl_options = {'REGISTER', 'UNDO'}

    first_mouse_x = 0
    first_mouse_y = 0

    def invoke(self, context, event):
        self.first_mouse_x = event.mouse_x
        self.first_mouse_y = event.mouse_y
        # print('x', self.first_mouse_x)
        # print('y', self.first_mouse_y)
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        if bpy.data.objects.get(bpy.context.scene.leftWindowObj) is not None:
            blender_executable = bpy.app.binary_path
            subprocess.Popen([blender_executable])
            return
        context.scene.rightEar_path = ""
        context.scene.leftEar_path = ""
        # 移动光标到屏幕中心
        context.window.cursor_warp(context.window.width // 2, (context.window.height // 2) + 60)
        bpy.ops.screen.userpref_show(section='SAVE_LOAD')
        # context.window.cursor_warp(self.first_mouse_x, self.first_mouse_y)
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


class Huier_OT_system(bpy.types.Operator):
    bl_idname = "huier.system"
    bl_label = "查看系统设置"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.screen.userpref_show(section='SYSTEM')
        return {'FINISHED'}


class Huier_OT_DaoChuWei(bpy.types.Operator):
    bl_idname = "huier.export"
    bl_label = "导出为"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        name = bpy.context.scene.leftWindowObj
        if bpy.data.objects.get(name) is None:
            return {'FINISHED'}
        # 将当前正在操作的物体提交
        current_tab = bpy.context.screen.areas[0].spaces.active.context
        submit_process = processing_stage_dict[current_tab]
        context.scene.lastprocess = submit_process
        override = getOverride()
        with bpy.context.temp_override(**override):
            recolor_and_change_mode(submit_process)
        register_globals()
        register_ui_globals()
        write_to_pickle()
        bpy.ops.wm.save_as_mainfile(filepath=context.scene.origin_expSedFile_path, check_existing=False)
        submit(submit_process)
        # 移动光标到屏幕中心
        context.window.cursor_warp(context.window.width // 2, (context.window.height // 2) + 60)
        bpy.ops.screen.userpref_show(section='ANIMATION')
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
        # 移动光标到屏幕中心
        context.window.cursor_warp(context.window.width // 2, (context.window.height // 2) + 60)
        bpy.ops.screen.userpref_show(section='FILE_PATHS')
        return {'FINISHED'}


# 自定义的新增菜单
class TOPBAR_MT_huierFile(bpy.types.Menu):
    bl_label = "文件"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_AREA'
        layout.operator("huier.new_file", text="新建", icon='FILE_NEW')
        layout.operator("import.sed_file", text="打开...", icon='FILE_FOLDER')

        layout.operator_context = 'EXEC_AREA' if context.blend_data.is_saved else 'INVOKE_AREA'
        layout.operator("save.sed_file", text="保存", icon='FILE_TICK')

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("save.sed_file", text="另存为")

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("huier.export", text="导出为", icon='EXPORT')
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


class IMPORT_OT_SedFile(bpy.types.Operator):
    bl_idname = "import.sed_file"
    bl_label = "选择 Sed 文件"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # 文件路径属性

    # 过滤文件扩展名
    filter_glob: bpy.props.StringProperty(
        default="*.sed",
        options={'HIDDEN'}
    )

    def hide_use_settings(self):
        # Check the most recent window (the file browser)
        window = bpy.context.window_manager.windows[-1]

        # Find the space of type `SpaceFileBrowser`
        for area in window.screen.areas:
            if area.ui_type != 'FILES':
                continue
            for space in area.spaces:
                if space.type != 'FILE_BROWSER':
                    continue

                # Hide the property settings region
                space.show_region_tool_props = False

    def execute(self, context):
        context.scene.expSedFile_path = self.filepath
        if len(self.filepath) > 0 and self.filepath.endswith('.sed'):
            name, _ = os.path.splitext(os.path.basename(self.filepath))
            context.scene.earname = name
            bpy.ops.wm.open_mainfile(filepath=self.filepath)
            ovverride1, ooverride2 = getOverrideInFlieBrowser()
            with bpy.context.temp_override(**ovverride1):
                import_sed_file()
        return {'FINISHED'}

    def invoke(self, context, event):
        if bpy.data.objects.get(bpy.context.scene.leftWindowObj) is not None:
            blender_executable = bpy.app.binary_path
            subprocess.Popen([blender_executable])
            return {'FINISHED'}
        # 打开文件选择器，初始路径为场景中存储的路径或默认路径
        context.window_manager.fileselect_add(self)
        bpy.app.timers.register(self.hide_use_settings, first_interval=0.2)
        return {'RUNNING_MODAL'}


class SAVE_OT_SedFile(bpy.types.Operator):
    bl_idname = "save.sed_file"
    bl_label = "保存为 Sed 文件"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # 文件路径属性

    filename_ext = ".sed"

    # 过滤文件扩展名
    filter_glob: bpy.props.StringProperty(
        default="*.sed",
        options={'HIDDEN'}
    )

    def hide_use_settings(self):
        # Check the most recent window (the file browser)
        window = bpy.context.window_manager.windows[-1]

        # Find the space of type `SpaceFileBrowser`
        for area in window.screen.areas:
            if area.ui_type != 'FILES':
                continue
            for space in area.spaces:
                if space.type != 'FILE_BROWSER':
                    continue

                # Hide the property settings region
                space.show_region_tool_props = False

    def execute(self, context):
        current_tab = bpy.context.screen.areas[0].spaces.active.context
        submit_process = processing_stage_dict[current_tab]
        context.scene.lastprocess = submit_process
        override = getOverride()
        with bpy.context.temp_override(**override):
            recolor_and_change_mode(submit_process)
        register_globals()
        register_ui_globals()
        write_to_pickle()
        if self.filepath == "":
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False)
        else:
            bpy.ops.wm.save_as_mainfile(filepath=self.filepath, check_existing=False)
        return {'FINISHED'}

    def invoke(self, context, event):
        # 打开文件选择器，初始路径为场景中存储的路径或默认路径
        context.window_manager.fileselect_add(self)
        self.filepath = context.scene.expSedFile_path
        bpy.app.timers.register(self.hide_use_settings, first_interval=0.2)
        return {'RUNNING_MODAL'}


def getOverrideInFlieBrowser():
    # 获取所有的窗口
    override = []
    for window in bpy.context.window_manager.windows:
        screen = window.screen

        # 在所有的窗口中找到3D视图
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                # print('宽度',area.width)
                if(area.spaces.active.use_local_collections == False):
                    # 设置local collection
                    area.spaces.active.use_local_collections = True
                ride = {
                    'window': window,
                    'screen': screen,
                    'area': area,
                    'region': [region for region in area.regions if region.type == 'WINDOW'][0],
                }
                override.append(ride)

    return override[0],override[1]


# ********** 3D视图下的菜单栏 **********

# 监听响应
def test():
    global left_last_dis, right_last_dis, left_last_rot, right_last_rot, left_last_loc, right_last_loc
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
            print('view_dis1', view_dis1)
            area2.spaces.active.region_3d.view_distance = view_dis1
            print('area2', area2.spaces.active.region_3d.view_distance)
            print('area1', area1.spaces.active.region_3d.view_distance)
            left_last_dis = view_dis1
            return
        elif view_dis2 != right_last_dis:
            print('view_dis2', view_dis1)
            area2.spaces.active.region_3d.view_distance = view_dis1
            print('area2', area2.spaces.active.region_3d.view_distance)
            print('area1', area1.spaces.active.region_3d.view_distance)
            right_last_dis = view_dis2
            return

        if view_loc1 != left_last_loc:
            new = mathutils.Vector((view_loc1[0], -view_loc1[1], view_loc1[2]))
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
        bpy.context.screen.areas[0].spaces.active.context = prev_context
        bpy.context.screen.areas[0].spaces.active.context = prev_context
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
                bpy.context.space_data.show_region_tool_header = False  # 隐藏工具栏
                # bpy.context.space_data.overlay.show_overlays = False
                bpy.context.space_data.overlay.show_object_origins = False  # 隐藏物体原点
                bpy.context.space_data.overlay.show_relationship_lines = False  # 隐藏父子物体间的连线
                bpy.context.space_data.overlay.show_outline_selected = False  # 隐藏选中物体的轮廓
                bpy.context.space_data.show_object_select_lattice = False  # 隐藏晶格物体
                bpy.context.space_data.show_region_hud = False  # 隐藏底部面板
                bpy.context.space_data.overlay.show_text = False  # 隐藏文本
                bpy.context.space_data.shading.use_studiolight_view_rotation = False  # 让世界空间照明跟随摄像机旋转
                bpy.context.space_data.shading.studiolight_intensity = 1.3  # 设置光照强度
                bpy.context.space_data.shading.studiolight_background_blur = 1  # 设置背景模糊
            with bpy.context.temp_override(**override[1]):
                bpy.ops.object.hide_collection(collection_index=2, extend=False)
                bpy.context.space_data.show_region_tool_header = False  # 隐藏工具栏
                # bpy.context.space_data.overlay.show_overlays = False
                bpy.context.space_data.overlay.show_object_origins = False  # 隐藏物体原点
                bpy.context.space_data.overlay.show_relationship_lines = False  # 隐藏父子物体间的连线
                bpy.context.space_data.overlay.show_outline_selected = False  # 隐藏选中物体的轮廓
                bpy.context.space_data.show_object_select_lattice = False  # 隐藏晶格物体
                bpy.context.space_data.show_region_hud = False  # 隐藏底部面板
                bpy.context.space_data.overlay.show_text = False  # 隐藏文本
                bpy.context.space_data.shading.use_studiolight_view_rotation = False  # 让世界空间照明跟随摄像机旋转
                bpy.context.space_data.shading.studiolight_intensity = 1.3  # 设置光照强度
                bpy.context.space_data.shading.studiolight_background_blur = 1  # 设置背景模糊

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
        bpy.context.screen.areas[0].spaces.active.context = prev_context
        bpy.context.screen.areas[0].spaces.active.context = prev_context
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

    # 如果检测到有modal正在运行则启动重启的modal
    if check_modals_running(bpy.context.scene.var, prev_context):
        set_mirror_context(True)
        bpy.ops.restart.modal('INVOKE_DEFAULT')
    # 切换布局时重绘右上角标识
    draw_font()
    # 回退操作
    # fallback(processing_stage_dict[prev_context])
    set_switch_flag(True)
    set_prev_context(prev_context)


class RestartModal(bpy.types.Operator):
    bl_idname = "restart.modal"
    bl_label = "重新启动正在运行的modal"

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global prev_context
        if not get_mirror_context():
            submit_process = processing_stage_dict[prev_context]
            var = bpy.context.scene.var
            if (submit_process == '打磨'):
                if var == 1:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.thickening('INVOKE_DEFAULT')
                elif var == 2:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.thinning('INVOKE_DEFAULT')
                elif var == 3:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.smooth('INVOKE_DEFAULT')
            elif (submit_process == '局部加厚'):
                if var == 5:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.obj.localthickeningaddarea('INVOKE_DEFAULT')
                elif var == 6:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.obj.localthickeningreducearea('INVOKE_DEFAULT')
                elif var == 7:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.obj.localthickeningthick('INVOKE_DEFAULT')
            elif (submit_process == '切割'):
                if var == 55:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.circlecut('INVOKE_DEFAULT')
                elif var == 56:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.stepcut('INVOKE_DEFAULT')
            elif (submit_process == '创建模具'):
                if var == 19:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.pointqiehuan('INVOKE_DEFAULT')
                elif var == 20:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.dragcurve('INVOKE_DEFAULT')
                elif var == 21:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.smoothcurve('INVOKE_DEFAULT')
            elif (submit_process == '传声孔'):
                if var == 23:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.soundcanalqiehuan('INVOKE_DEFAULT')
            elif (submit_process == '通气孔'):
                if var == 26:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.ventcanalqiehuan('INVOKE_DEFAULT')
            elif (submit_process == '耳膜附件'):
                if var != 16:
                    if var == 14:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.object.handleswitch('INVOKE_DEFAULT')
                    else:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.wm.tool_set_by_id(name="my_tool.handle_initial")
            elif (submit_process == '编号'):
                if var != 43:
                    if var == 41:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.object.labelswitch('INVOKE_DEFAULT')
                    else:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.wm.tool_set_by_id(name="my_tool.label_initial")
            elif (submit_process == '支撑'):
                if var != 78:
                    if var == 77:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.object.supportswitch('INVOKE_DEFAULT')
                    else:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.wm.tool_set_by_id(name="my_tool.support_initial")
            elif (submit_process == '排气孔'):
                if var != 89:
                    if var == 87:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.object.sprueswitch('INVOKE_DEFAULT')
                    else:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.wm.tool_set_by_id(name="my_tool.sprue_initial")
            elif (submit_process == '后期打磨'):
                if var == 111:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.last_thickening('INVOKE_DEFAULT')
                elif var == 112:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.last_thinning('INVOKE_DEFAULT')
                elif var == 113:
                    override = getOverride()
                    with bpy.context.temp_override(**override):
                        bpy.ops.object.last_smooth('INVOKE_DEFAULT')
            elif (submit_process == '切割模具'):
                if var != 91:
                    if var == 90:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch1")
                    else:
                        override = getOverride()
                        with bpy.context.temp_override(**override):
                            bpy.ops.wm.tool_set_by_id(name="tool.cutmouldswitch2")
            return {'FINISHED'}
        return {'PASS_THROUGH'}


# 给3d区域添加监听器
# SpaceView3D.my_handler = SpaceView3D.draw_handler_add(test, (), 'WINDOW', 'PRE_VIEW')


# 切换左右耳窗口
class Huier_OT_SwitchWorkspace(bpy.types.Operator):
    bl_idname = "huier.switch"
    bl_label = "切换窗口"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rightWindowObj = bpy.data.objects.get("右耳")
        leftWindowObj = bpy.data.objects.get("左耳")
        if leftWindowObj != None and rightWindowObj != None:
            # bpy.context.scene.var = 0   # 退出所有模态
            global prev_context
            set_switch_flag(False)

            global is_listen_start
            if not is_listen_start:
                is_listen_start = True
                # 监听workspace切换到左右耳窗口
                subscribe_to = bpy.types.Window, 'workspace'
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
                prev_context = bpy.context.screen.areas[0].spaces.active.context
                bpy.context.window.workspace = bpy.data.workspaces['布局.001']
                # 获取"MyCollection"的LayerCollection对象
                my_layer_collection = get_layer_collection(bpy.context.view_layer.layer_collection, 'Right')
                # 将"MyCollection"设置为活动层集合
                if my_layer_collection:
                    bpy.context.view_layer.active_layer_collection = my_layer_collection

            if bpy.context.window.workspace.name == '布局.001':
                # 保存之前窗口的模式
                prev_context = bpy.context.screen.areas[0].spaces.active.context
                bpy.context.window.workspace = bpy.data.workspaces['布局']

        return {'FINISHED'}


class VIEW3D_HT_header(bpy.types.Header):
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        name = bpy.context.scene.leftWindowObj
        layout = self.layout
        icons = load_icons()  # 标题栏自制图标

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
        if name == '右耳':
            row.active = (bpy.data.objects.get(name + "OriginForShow") != None)
            row.prop(context.scene, "transparent1R", text="", icon_value=icon.icon_id, icon_only=True)
            sub = row.row(align=True)
            sub.popover("TOPBAR_PT_transparency1", text="")
        elif name == '左耳':
            row.active = (bpy.data.objects.get(name + "OriginForShow") != None)
            row.prop(context.scene, "transparent1L", text="", icon_value=icon.icon_id, icon_only=True)
            sub = row.row(align=True)
            sub.popover("TOPBAR_PT_transparency1", text="")

        row = layout.row(align=True)
        icon = icons.get("icon_transparency2")
        if name == '右耳':
            row.active = ((bpy.data.objects.get(name + "WaxForShow") != None) or
                          (bpy.data.objects.get(name) != None and bpy.context.screen.areas[
                              1].spaces.active.context == 'RENDER') or
                          ((bpy.data.objects.get(name) != None and bpy.context.screen.areas[
                              1].spaces.active.context == 'MATERIAL') and get_color_mode() == 1))
            row.prop(context.scene, "transparent2R", text="", icon_value=icon.icon_id, icon_only=True)
            sub = row.row(align=True)
            sub.popover("TOPBAR_PT_transparency2", text="")
        elif name == '左耳':
            row.active = ((bpy.data.objects.get(name + "WaxForShow") != None) or
                          (bpy.data.objects.get(name) != None and bpy.context.screen.areas[
                              1].spaces.active.context == 'RENDER') or
                          ((bpy.data.objects.get(name) != None and bpy.context.screen.areas[
                              1].spaces.active.context == 'MATERIAL') and get_color_mode() == 1))
            row.prop(context.scene, "transparent2L", text="", icon_value=icon.icon_id, icon_only=True)
            sub = row.row(align=True)
            sub.popover("TOPBAR_PT_transparency2", text="")

        row = layout.row(align=True)
        icon = icons.get("icon_transparency3")
        if name == '右耳':
            current_process = processing_stage_dict[bpy.context.screen.areas[0].spaces.active.context]
            row.active = order_processing_list.index(current_process) > 0
            row.prop(context.scene, "transparent3R", text="", icon_value=icon.icon_id, icon_only=True)
            sub = row.row(align=True)
            sub.popover("TOPBAR_PT_transparency3", text="")
        elif name == '左耳':
            current_process = processing_stage_dict[bpy.context.screen.areas[0].spaces.active.context]
            row.active = order_processing_list.index(current_process) > 0
            row.prop(context.scene, "transparent3L", text="", icon_value=icon.icon_id, icon_only=True)
            sub = row.row(align=True)
            sub.popover("TOPBAR_PT_transparency3", text="")

        row = layout.row(align=True)
        row.separator()
        row.separator()
        row.separator()
        row.separator()
        row.ui_units_x = 10
        row.prop(context.scene, "earname", text="")


# 测试按钮功能
class HUIER_PT_TestButton(bpy.types.Panel):
    bl_label = "按钮测试"
    bl_idname = "HUIER_PT_Button"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "3DModel"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("object.msgbuscallback", text="初始化模块切换")
        col.operator("object.msgbuscallback2", text="暂停模块切换")
        col.operator("object.msgbuscallback3", text="开始模块切换")
        col.operator("obj.undo1", text="撤回")
        col.operator("obj.redo1", text="前进")


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
            x = area.x + int(area.width / 2)
            y = area.y + area.height + 3
            w.cursor_warp(x, y)
            if show_prop == False:
                delta = 300 - area.height
                show_prop = True
            else:
                delta = -area.height + 1
                show_prop = False
            bpy.app.timers.register(functools.partial(snooper, context.copy(), w, initx, inity, x, y, delta=delta),
                                    first_interval=0.2)

        return {'FINISHED'}


def snooper(c, w, initx, inity, x, y, delta):
    global show_prop
    poll_retries = 100
    while not bpy.ops.screen.area_move.poll():
        # show_prop = not show_prop
        poll_retries -= 1
        if not poll_retries:
            return None  # out of retries

    # 移动边界
    bpy.ops.screen.area_move(x=x, y=y, delta=delta)

    # 光标移动回按钮点击位置
    w.cursor_warp(initx, inity)
    return None


def submit(submit_process):
    if bpy.context.scene.leftWindowObj == '右耳':
        mat = bpy.data.materials.get("YellowR")
    elif bpy.context.scene.leftWindowObj == '左耳':
        mat = bpy.data.materials.get("YellowL")
    if (submit_process == '打磨'):
        pass
    elif (submit_process == '局部加厚'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.obj.localthickeningsubmit('INVOKE_DEFAULT')
    elif (submit_process == '切割'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.finishcut('INVOKE_DEFAULT')
    elif (submit_process == '创建模具'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.finishmould('INVOKE_DEFAULT')
    elif (submit_process == '传声孔'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.finishsoundcanal('INVOKE_DEFAULT')
    elif (submit_process == '通气孔'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.finishventcanal('INVOKE_DEFAULT')
    elif (submit_process == '耳膜附件'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.handlesubmit('INVOKE_DEFAULT')
    elif (submit_process == '编号'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.labelsubmit('INVOKE_DEFAULT')
    elif (submit_process == '铸造法软耳模'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.castingsubmit('INVOKE_DEFAULT')
            # 为铸造法外壳添加透明材质
            name = bpy.context.scene.leftWindowObj
            casting_name = name + "CastingCompare"
            casting_compare_obj = bpy.data.objects.get(casting_name)
            if (casting_compare_obj != None):
                mat.blend_method = 'BLEND'
                if name == '右耳':
                    bpy.context.scene.transparent3EnumR = 'OP3'
                elif name == '左耳':
                    bpy.context.scene.transparent3EnumL = 'OP3'
    elif (submit_process == '支撑'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.supportsubmit('INVOKE_DEFAULT')
            # 为铸造法外壳添加透明材质
            name = bpy.context.scene.leftWindowObj
            casting_name = name + "CastingCompare"
            casting_compare_obj = bpy.data.objects.get(casting_name)
            if (casting_compare_obj != None):
                mat.blend_method = 'BLEND'
                if name == '右耳':
                    bpy.context.scene.transparent3EnumR = 'OP3'
                elif name == '左耳':
                    bpy.context.scene.transparent3EnumL = 'OP3'
    elif (submit_process == '排气孔'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.spruesubmit('INVOKE_DEFAULT')
            # 为铸造法外壳添加透明材质
            mat.blend_method = 'BLEND'
            if bpy.context.scene.leftWindowObj == '右耳':
                bpy.context.scene.transparent3EnumR = 'OP3'
            elif bpy.context.scene.leftWindowObj == '左耳':
                bpy.context.scene.transparent3EnumL = 'OP3'
    elif (submit_process == '后期打磨'):
        override = getOverride()
        with bpy.context.temp_override(**override):
            bpy.ops.object.last_damo_finish('INVOKE_DEFAULT')


def recolor_and_change_mode(submit_process):
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.context.scene.leftWindowObj]
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[bpy.context.scene.leftWindowObj].select_set(state=True)
    if submit_process == '打磨':
        # 重新着色
        active_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
        # 获取网格数据
        me = active_obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            colvert.x = 0
            colvert.y = 0.25
            colvert.z = 1

        bm.to_mesh(me)
        bm.free()

    elif submit_process == '后期打磨':
        # 重新着色
        active_obj = bpy.data.objects[bpy.context.scene.leftWindowObj]
        # 获取网格数据
        me = active_obj.data
        # 创建bmesh对象
        bm = bmesh.new()
        # 将网格数据复制到bmesh对象
        bm.from_mesh(me)
        color_lay = bm.verts.layers.float_color["Color"]
        for vert in bm.verts:
            colvert = vert[color_lay]
            colvert.x = 1
            colvert.y = 0.319
            colvert.z = 0.133

        bm.to_mesh(me)
        bm.free()


# 注册类
_classes = [
    # VIEW3D_HT_header,
    HUIER_PT_damo,
    HUIER_PT_LocalOrGlobalJiaHou,
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
    TOPBAR_MT_huierFile,
    TOPBAR_MT_huierView,
    # TOPBAR_MT_file,
    # TOPBAR_MT_edit,
    HUIER_PT_TestButton,
    Huier_OT_addon,
    Huier_OT_keymap,
    Huier_OT_system,
    Huier_OT_NewFile,
    Huier_OT_DaoChuWei,
    Huier_OT_SaveAsMoban,
    HUIER_PT_MoJuTab,
    HUIER_PT_MoBanXuanZe,
    Huier_OT_SwitchWorkspace,
    ToggleProperty,
    HUIER_PT_CutMould,
    RestartModal,
    IMPORT_OT_SedFile,
    SAVE_OT_SedFile
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
