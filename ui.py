# ------------------------------------------------------
#
# UI
#
# ------------------------------------------------------
#  .XXX代表与该文件同级的文件，    ..XXX代表与带文件父目录同级的文件
import bpy
import os
import bpy.utils.previews
from .jiahou import *
from .damo import *
import bpy_extras
from bpy_extras.io_utils import ImportHelper
from .icon.icons import load_icons
from .icon.icons import clear_icons


import mathutils
import bmesh
from bpy_extras import view3d_utils


# 打磨面板
class huier_PT_damo(bpy.types.Panel):

    bl_label = "耳样处理"
    bl_idname = "HUIER_PT_damo"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        layout.scale_x = 1.2
        layout.use_property_split = True
        layout.use_property_decorate = False
        # flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)
        col = layout.column()
        col.prop(context.scene, 'laHouDU', text="蜡厚度")
        col.prop(context.scene, 'localLaHouDu', text="局部蜡厚度限制")
        col = layout.column()
        col.active = context.scene.localLaHouDu
        col.prop(context.scene, 'maxLaHouDu', text="最大蜡厚度")
        col.prop(context.scene, 'minLaHouDu', text="最小蜡厚度")

        # box = layout.box()
        # box.prop(context.scene, 'laHouDU', text="蜡厚度")
        # lahoudu(self,context,box)

# def lahoudu(self,context,box):
#     box.prop(context.scene,'localLaHouDu', text="局部蜡厚度限制",
#              icon='TRIA_UP' if context.scene.localLaHouDu else 'TRIA_RIGHT')
#     if context.scene.localLaHouDu:
#         box.prop(context.scene, 'maxLaHouDu', text="最大蜡厚度")
#         box.prop(context.scene, 'minLaHouDu', text="最小蜡厚度")


# 局部或整体加厚面板
class CustomPanelLocalOrGlobalJiaHou(bpy.types.Panel):
    bl_label = "局部或整体加厚"
    bl_idname = "CustomPanelLocalOrGlobalJiaHou"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "output"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'pianYiZhi', text="偏移值")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'bianKuangKuanDu', text="边框宽度")
        # col = layout.column(align=True)
        # col.operator("object.rightmouse", text="鼠标行为")


# 点面切割
class CustomPanelDianMianQieGe(bpy.types.Panel):
    bl_label = "选择工具"
    bl_idname = "CustomPanelDianMianQieGe"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'qieGeTypeEnum', text="选择工具")


class CustomPanelPlantCut(bpy.types.Panel):
    bl_label = "plant cut平面切割"
    bl_idname = "CustomPanelPlantCut"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'sheRuPianYi', text="舍入偏移")
        layout.separator()


class CustomPanelStepCut(bpy.types.Panel):
    bl_label = "step vent 阶梯状切割"
    bl_idname = "CustomPanelStepCut"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'waiBianYuanSheRuPianYi', text="外边缘平滑偏移")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'neiBianYuanSheRuPianYi', text="内边缘平滑偏移")


# 创建模具
class CustomPaneChuangJianMuJu(bpy.types.Panel):
    bl_label = "创建模具"
    bl_idname = "CustomPaneChuangJianMuJu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'muJuTypeEnum', text="模具类型")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'neiBianJiXian', text="内编辑线")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'waiBianYuanSheRuPianYi', text="外舍入偏移")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'neiBianYuanSheRuPianYi', text="内舍入偏移")


class CustomPanelMuJuHouDu(bpy.types.Panel):
    bl_label = "模具厚度"
    bl_idname = "CustomPanelMuJuHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'zongHouDu', text="总厚度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'jiHuoBianYuanHouDu', text="激活边缘厚度")


class CustomPanelBianYuanHouDu(bpy.types.Panel):
    bl_label = "边缘厚度"
    bl_idname = "CustomPanelBianYuanHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_parent_id = "CustomPanelMuJuHouDu"

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
        col.prop(context.scene, 'zhongJianQuYuKuanDu', text="中间区域宽度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'neiBuHouDu', text="内部厚度")


class CustomPanelMianBanAndDianZiSheBei(bpy.types.Panel):
    bl_label = "面板和电子设备"
    bl_idname = "CustomPanelMianBanAndDianZiSheBei"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

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


class CustomPanelShangBuQieGeMianBan(bpy.types.Panel):
    bl_label = "上部切割面板"
    bl_idname = "CustomPanelShangBuQieGeMianBan"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shiFouShangBuQieGeMianBan', text="上部切割面板")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shangBuQieGeMianBanPianYi', text="上部切割面板偏移")


class CustomPanelKongQiangMianBan(bpy.types.Panel):
    bl_label = "空腔面板"
    bl_idname = "CustomPanelKongQiangMianBan"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'shiFouKongQiangMianBan', text="空腔面板")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'KongQiangMianBanSheRuPianYi', text="空腔面板舍入")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'ShangBuQieGeBanPianYi', text="上部切割板偏移")


class CustomPanelYingErMoCanShu(bpy.types.Panel):
    bl_label = "硬耳膜参数"
    bl_idname = "CustomPanelYingErMoCanShu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'gongXingMianBan', text="拱形面板")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'gongKuan', text="拱宽")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'gongGao', text="拱高")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'yingErMoSheRuPianYi', text="舍入偏移")


class CustomPanelTongQiKong1(bpy.types.Panel):
    bl_label = "通气孔"
    bl_idname = "CustomPanelTongFengKou"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

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


# 传声孔
class CustomPanelChuanShenKong1(bpy.types.Panel):
    bl_label = "传声孔"
    bl_idname = "CustomPanelChuanShenKong1"
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


class CustomPanelChuanShenKong2(bpy.types.Panel):
    bl_label = "faceplate opening面板开口"
    bl_idname = "CustomPanelChuanShenKong2"
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
class CustomPanelTongQiKong(bpy.types.Panel):
    bl_label = "通气孔"
    bl_idname = "CustomPanelTongQiKong"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "collection"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'tongQiGuanDaoZhiJing', text="管道直径")


# 耳膜附件
class CustomPanelErMoFuJian(bpy.types.Panel):
    bl_label = "耳膜附件"
    bl_idname = "CustomPanelErMoFuJian"
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
class CustomPanelNumber(bpy.types.Panel):
    bl_label = "编号"
    bl_idname = "CustomPanelNumber"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "modifier"

    def draw(self, context):
        layout = self.layout
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
class CustomPanelRuanErMoHouDu(bpy.types.Panel):
    bl_label = "软耳模厚度"
    bl_idname = "CustomPanelRuanErMoHouDu"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "particle"

    def draw(self, context):
        layout = self.layout
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'fontSize', text="字体尺寸")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'deep', text="深度")
        layout.separator()
        col = layout.column(align=True)
        col.prop(context.scene, 'styleEnum', text="风格")


# 支撑
class CustomPanelZhiCheng(bpy.types.Panel):
    bl_label = "支撑"
    bl_idname = "CustomPanelZhiCheng"
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
class CustomPanelPaiQiKong(bpy.types.Panel):
    bl_label = "排气孔"
    bl_idname = "CustomPanelPaiQiKong"
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
class CustomPanelHouQiDaMo(bpy.types.Panel):
    bl_label = "后期打磨"
    bl_idname = "CustomPanelHouQiDaMo"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

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
class TOPBAR_MT_transparency1(bpy.types.Panel):
    bl_label = "透明度1"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        layout.operator("wm.open_mainfile", text="自动...", icon='FILE_FOLDER')
        layout.ui_units_x = 5
        layout.separator()
        layout.operator("wm.save_mainfile", text="不透明", icon='FILE_TICK')

        layout.separator()
        layout.operator("wm.save_mainfile", text="透明", icon='FILE_TICK')

        layout.separator()
        layout.menu("TOPBAR_MT_file_import", text="透明比例", icon='IMPORT')
# 透明度2


class TOPBAR_MT_transparency2(bpy.types.Panel):
    bl_label = "透明度2"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 5
        layout.operator("wm.open_mainfile", text="自动...", icon='FILE_FOLDER')

        layout.separator()
        layout.operator("wm.save_mainfile", text="不透明", icon='FILE_TICK')

        layout.separator()
        layout.operator("wm.save_mainfile", text="透明", icon='FILE_TICK')

        layout.separator()
        layout.menu("TOPBAR_MT_file_import", text="透明比例", icon='IMPORT')

# 透明度3


class TOPBAR_MT_transparency3(bpy.types.Panel):
    bl_label = "透明度3"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        layout.ui_units_x = 5
        layout.operator("wm.open_mainfile", text="自动...", icon='FILE_FOLDER')

        layout.separator()
        layout.operator("wm.save_mainfile", text="不透明", icon='FILE_TICK')

        layout.separator()
        layout.operator("wm.save_mainfile", text="透明", icon='FILE_TICK')

        layout.separator()
        layout.menu("TOPBAR_MT_file_import", text="透明比例", icon='IMPORT')


# 第一行的菜单
class TOPBAR_MT_editor_menus(bpy.types.Menu):
    bl_idname = "TOPBAR_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        layout.menu("TOPBAR_MT_huierFile")
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
        layout.menu("TOPBAR_MT_file_open_recent")

        layout.separator()

        layout.operator_context = 'EXEC_AREA' if context.blend_data.is_saved else 'INVOKE_AREA'
        layout.operator("wm.save_mainfile", text="保存", icon='FILE_TICK')

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_as_mainfile", text="另存为...")
        layout.operator_context = 'INVOKE_AREA'

        layout.separator()

        layout.menu("TOPBAR_MT_file_import", icon='IMPORT')
        layout.menu("TOPBAR_MT_file_export", icon='EXPORT')


class OT_ImportFile(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """select file path"""
    bl_idname = "huier.import"
    bl_label = "Import Data"
    bl_options = {'REGISTER', 'UNDO'}

    # # 过滤限制可选择的文件扩展名
    filter_glob: bpy.props.StringProperty(
        default='*.stl',
        options={'HIDDEN'},
        maxlen=255,
    )

    """use_setting: bpy.props.BoolProperty(
        name="Example Boolean", 
        description="Example Tooltip", 
        default=True,
    )"""

    def execute(self, context):
        filePath = self.filepath
        # 导入STL文件
        bpy.ops.wm.stl_import(filepath=filePath)
        # 将模型移到视图中心
        bpy.ops.object.select_all(action='SELECT')
        # bpy.ops.view3d.snap_cursor_to_center()
        # bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        # bpy.ops.object.location_clear(clear_delta=False)
        # 将模型颜色设置成黄色
        # mat = newShader("Yellow", "principled", 0.58, 0.16, 0.05)
        # obj = bpy.context.active_object
        # obj.data.materials.clear()
        # obj.data.materials.append(mat)
        # bpy.data.screens["Layout"].shading.type = 'MATERIAL'
        return {'FINISHED'}

# 自定义的新增菜单


class TOPBAR_MT_huierFile(bpy.types.Menu):
    bl_label = "文件"

    def draw(self, context):
        layout = self.layout
        layout.operator(OT_ImportFile.bl_idname, text="新建", icon='FILE_NEW')


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


# ********** 3D视图下的菜单栏 **********

class VIEW3D_HT_header(bpy.types.Header):
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        layout = self.layout
        icons = load_icons()  # 标题栏自制图标
        icon = icons.get("icon_backup")
        layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_forward")
        layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_grid")
        layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_ruler")
        layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_viewShift")
        layout.operator("wm.open_mainfile", text="", icon_value=icon.icon_id)
        icon = icons.get("icon_transparency1")
        layout.popover("TOPBAR_MT_transparency1",
                       text="", icon_value=icon.icon_id)
        icon = icons.get("icon_transparency2")
        layout.popover("TOPBAR_MT_transparency2",
                       text="", icon_value=icon.icon_id)
        icon = icons.get("icon_transparency3")
        layout.popover("TOPBAR_MT_transparency3",
                       text="", icon_value=icon.icon_id)


# 测试按钮功能
class CustomPanelTestButton(bpy.types.Panel):
    bl_label = "按钮测试"
    bl_idname = "testButton"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TestButton"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("obj.initialcolor", text="初始化模型颜色")
        # col.operator("obj.initialtransparency",text="透明")
        # col.operator("obj.localreset",text="重置")
        # col.operator("obj.addarea",text="扩大区域")
        # col.operator("obj.reducearea",text="缩小区域")
        # col.operator("obj.local_thickening",text="加厚")
        # col.operator("sculpt.brush_stroke",text="+")
        # col.operator("obj.local_submit",text="提交")


# 注册类
_classes = [
    # VIEW3D_HT_header,
    huier_PT_damo,
    CustomPanelLocalOrGlobalJiaHou,
    CustomPanelDianMianQieGe,
    CustomPanelPlantCut,
    CustomPanelStepCut,
    CustomPaneChuangJianMuJu,
    CustomPanelMuJuHouDu,
    CustomPanelBianYuanHouDu,
    CustomPanelMianBanAndDianZiSheBei,
    CustomPanelShangBuQieGeMianBan,
    CustomPanelKongQiangMianBan,
    CustomPanelYingErMoCanShu,
    CustomPanelTongQiKong1,
    CustomPanelChuanShenKong1,
    CustomPanelChuanShenKong2,
    CustomPanelTongQiKong,
    CustomPanelErMoFuJian,
    CustomPanelNumber,
    CustomPanelRuanErMoHouDu,
    CustomPanelZhiCheng,
    CustomPanelPaiQiKong,
    CustomPanelHouQiDaMo,
    # TOPBAR_HT_upper_bar,
    # TOPBAR_MT_transparency1,
    # TOPBAR_MT_transparency2,
    # TOPBAR_MT_transparency3,
    # TOPBAR_MT_editor_menus,
    TOPBAR_MT_screteEarFile,
    TOPBAR_MT_huierFile,
    TOPBAR_MT_file,
    TOPBAR_MT_edit,
    CustomPanelTestButton,
    OT_ImportFile
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in _classes:
        bpy.utils.unregister_class(cls)
