import bpy
import blf
from .damo import *
from .jiahou import *
from .qiege import *
from .label import *
from .support import *
from .create_mould.soft_eardrum.thickness_and_fill import reset_and_refill
from .create_mould.soft_eardrum.soft_eardrum import apply_soft_eardrum_template
from .create_mould.frame_style_eardrum.frame_style_eardrum import apply_frame_style_eardrum_template
from .create_mould.create_mould import recover

import os

font_info = {
    "font_id": 0,
    "handler": None,
}

flag = True


def My_Properties():
    # 全局变量,多个模块的文件共享该全局变量,各个模式的按钮都会有一个var值,当该按钮处于其对应的值时,会运行其操作符,不再其对应值时,会自动结束该操作符
    # 默认var值为0,各个操作符都未启动
    # 打磨模块:       打磨加厚按钮: 1        打磨打薄按钮:  2      打磨平滑按钮:  3       打磨重置按钮:  4
    # 局部加厚模块:   局部加厚重置: 9        局部加厚扩大区域: 5       局部加厚缩小区域: 6        局部加厚加厚: 7    局部加厚提交: 8
    # 切割模块:由于切割模式在初始化时会自动进入切割模态,退出时自动退出切割模块,故切割模块未使用该变量
    bpy.types.Scene.var = bpy.props.IntProperty(
        name="var", default=0, description="每个模块的按钮都会对应一个var值,用于结束按钮的modal"
    )

    # 打磨操作属性      蜡厚度，局部蜡厚度限制，最大蜡厚度，最小蜡厚度
    bpy.types.Scene.laHouDU = bpy.props.FloatProperty(
        name="laHouDU", min=-2.0, max=2.0, step=5,
        description="调整蜡厚度的大小", update=Houdu)
    bpy.types.Scene.localLaHouDu = bpy.props.BoolProperty(
        name="localLaHouDu", default=False)
    bpy.types.Scene.maxLaHouDu = bpy.props.FloatProperty(
        name="maxLaHouDu", min=-1.0, max=1.0, step=1, description="最大蜡厚度的值")
    bpy.types.Scene.minLaHouDu = bpy.props.FloatProperty(
        name="minLaHouDu", min=-1.0, max=1.0, step=1, description="最小蜡厚度的值")

    # 局部或整体加厚    偏移值，边框宽度
    bpy.types.Scene.localThicking_offset = bpy.props.FloatProperty(
        name="localThicking_offset", min=0, max=3.0, default=0.8, update=LocalThickeningOffsetUpdate)
    bpy.types.Scene.localThicking_borderWidth = bpy.props.FloatProperty(
        name="localThicking_borderWidth", min=0, max=3.0, default=0.8, update=LocalThickeningBorderWidthUpdate)
    bpy.types.Scene.is_thickening_completed = bpy.props.BoolProperty(
        name="is_thickening_completed")  # 防止局部加厚中的参数更新过快使得加厚参数调用的过于频繁,使得物体发生形变

    # 点面切割属性
    bpy.types.Scene.qieGeTypeEnum = bpy.props.EnumProperty(
        name="",
        description='this is option',
        items=[
            ('OP1', '平面切割', ''),
            ('OP2', '阶梯状切割', '')],
        update=qiegeenum
    )
    bpy.types.Scene.qiegesheRuPianYi = bpy.props.FloatProperty(
        name="sheRuPianYi", min=0.0, max=1.0, step=1, default=0.5, update=sheru)

    bpy.types.Scene.qiegewaiBianYuan = bpy.props.FloatProperty(
        name="qiegewaiBianYuan", min=0.1, max=3,
        step=10)
    bpy.types.Scene.qiegeneiBianYuan = bpy.props.FloatProperty(
        name="qiegeneiBianYuan", min=0.1, max=3, step=10, update=qiegesmooth2, default=0.4)

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
                                                                default="right.stl",
                                                                maxlen=1024,
                                                                subtype="FILE_PATH")

    bpy.types.Scene.expLeftEar_path = bpy.props.StringProperty(name="",
                                                               description="左耳输出",
                                                               default="left.stl",
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
                                                         default="软耳模",
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
        update=ChangeMouldType
    )
    bpy.types.Scene.neiBianJiXian = bpy.props.BoolProperty(
        name="neiBianJiXian")
    bpy.types.Scene.waiBianYuanSheRuPianYi = bpy.props.FloatProperty(
        name="waiBianYuanSheRuPianYi", min=0.0, max=3.0, update=CreateMouldOuterSmooth)
    bpy.types.Scene.neiBianYuanSheRuPianYi = bpy.props.FloatProperty(
        name="neiBianYuanSheRuPianYi", min=0.0, max=3.0, update=CreateMouldInnerSmooth)

    bpy.types.Scene.zongHouDu = bpy.props.FloatProperty(
        name="zongHouDu", min=0.0, max=5.0, default=1.0, update=CreateMouldThicknessUpdate)
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
        name="shiFouKongQiangMianBan")
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
    bpy.types.Scene.yingErMoSheRuPianYi = bpy.props.FloatProperty(
        name="yingErMoSheRuPianYi", min=-1.0, max=1.0)
    bpy.types.Scene.shiFouTongFengGuan = bpy.props.BoolProperty(
        name="shiFouTongFengGuan")
    bpy.types.Scene.tongFengGuanZhiJing = bpy.props.FloatProperty(
        name="tongFengGuanZhiJing", min=-1.0, max=1.0)
    bpy.types.Scene.tongFengGuanHouDu = bpy.props.FloatProperty(
        name="tongFengGuanHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.tongFengGuanWaiBuHouDu = bpy.props.FloatProperty(
        name="tongFengGuanWaiBuHouDu", min=-1.0, max=1.0)

    # 传声孔      管道平滑      传声管道直径         激活   管道形状  偏移
    bpy.types.Scene.gaunDaoPinHua = bpy.props.BoolProperty(
        name="gaunDaoPinHua")
    bpy.types.Scene.chuanShenGuanDaoZhiJing = bpy.props.FloatProperty(
        name="chuanShenGuanDaoZhiJing", min=-1.0, max=1.0)
    bpy.types.Scene.active = bpy.props.BoolProperty(name="active")
    bpy.types.Scene.chuanShenKongOffset = bpy.props.FloatProperty(
        name="chuanShenKongOffset", min=-1.0, max=1.0)
    bpy.types.Scene.shapeEnum = bpy.props.EnumProperty(
        name="shapeEnum",
        description='传声孔的形状',
        items=[
            ('OP1', '号角管1', ''),
            ('OP2', '号角管2', ''),
            ('OP3', '传声管1', ''),
            ('OP4', '传声管2', ''),
            ('OP5', '铜扣', ''),
            ('OP6', 'S喇叭', ''),
            ('OP7', 'M喇叭', ''),
            ('OP8', 'P喇叭', ''),
            ('OP9', 'SP喇叭', ''),
            ('OP10', 'RIC启敏喇叭', ''),
            ('OP11', 'HP喇叭', ''),
            ('OP12', '听诊器耳塞', '')]
    )

    # 通气孔     通气管道直径
    bpy.types.Scene.tongQiGuanDaoZhiJing = bpy.props.FloatProperty(
        name="tongQiGuanDaoZhiJing", min=-1.0, max=1.0)

    # 耳膜附件      耳膜附件类型    偏移
    bpy.types.Scene.erMoFuJianOffset = bpy.props.FloatProperty(
        name="erMoFuJianOffset", min=-1.0, max=1.0)
    bpy.types.Scene.erMoFuJianTypeEnum = bpy.props.EnumProperty(
        name="erMoFuJianTypeEnum",
        description='handle耳膜附件的类型',
        items=[
            ('OP1', '耳膜附件', ''),
        ]
    )

    # 编号
    bpy.types.Scene.labelText = bpy.props.StringProperty(
        name="labelText", description="Enter label text here", default="HDU", update=LabelTextUpdate)
    bpy.types.Scene.fontSize = bpy.props.IntProperty(
        name="fontSize", min=1, max=8, default=4, update=LabelSizeUpdate)
    bpy.types.Scene.deep = bpy.props.FloatProperty(
        name="deep", min=0.0, max=3.0, default=1.0, update=LabelDepthUpdate)
    bpy.types.Scene.styleEnum = bpy.props.EnumProperty(
        name="styleEnum",
        description='编号的风格',
        items=[
            ('OP1', '内嵌', ''),
            ('OP2', '外凸', ''), ],
        update=LabelEnum
    )

    # 软耳模厚度       厚度类型    软耳模厚度
    bpy.types.Scene.ruanErMoHouDu = bpy.props.FloatProperty(
        name="ruanErMoHouDu", min=-1.0, max=1.0)
    bpy.types.Scene.ruanErMoTypeEnum = bpy.props.EnumProperty(
        name="ruanErMoTypeEnum",
        description='',
        items=[
            ('OP1', '偏移曲面', ''),
            ('OP2', '无', ''), ]
    )

    # 支撑        支撑类型     偏移
    bpy.types.Scene.zhiChengOffset = bpy.props.FloatProperty(
        name="zhiChengOffset", min=-1.0, max=1.0, update=SupportOffsetUpdate)
    bpy.types.Scene.zhiChengTypeEnum = bpy.props.EnumProperty(
        name="zhiChengTypeEnum",
        description='',
        items=[
            ('OP1', '硬耳模支撑', ''),
            ('OP2', '软耳膜支撑', ''), ],
        update=SupportEnum
    )

    # 排气孔        排气孔类型     偏移
    bpy.types.Scene.paiQiKongOffset = bpy.props.FloatProperty(
        name="paiQiKongOffset", min=-1.0, max=1.0)
    bpy.types.Scene.paiQiKongTypeEnum = bpy.props.EnumProperty(
        name="paiQiKongTypeEnum",
        description='',
        items=[
            ('OP1', '排气孔', ''), ]
    )


# 添加厚度修改器
def modify(self, context, thickness):
    global flag
    context1 = bpy.context.space_data.context
    if flag == True and context1 == 'RENDER':
        flag = False
        obj = bpy.context.active_object
        md = obj.modifiers.new("jiahou", "SOLIDIFY")
        md.use_rim_only = True
        md.use_quality_normals = True
        md.offset = 1
        md.thickness = context.scene.laHouDU
        return {'RUNNING_MODAL'}
    else:
        if thickness < 0:
            name = bpy.context.active_object.name
            md = bpy.data.objects[name].modifiers["jiahou"]
            md.use_flip_normals = True

        else:
            name = bpy.context.active_object.name
            md = bpy.data.objects[name].modifiers["jiahou"]
            md.use_flip_normals = False
        return {'FINISHED'}


def Houdu(self, context):
    bl_description = "初始耳模的厚度"
    thickness = context.scene.laHouDU
    modify(self, context, thickness)
    active_object = bpy.context.active_object
    name = active_object.name
    bpy.data.objects[name].modifiers["jiahou"].thickness = thickness
    # MyHandleClass.remove_handler()
    # MyHandleClass.add_handler(draw_callback_px, (None, thickness))


def sheru(self, context):
    bl_description = ""
    smooth()


def another_filename(filename):
    if filename.endswith('L.stl'):
        # 如果是，将'L.stl'替换为'R.stl'
        return filename.replace('L.stl', 'R.stl')
    # 检查文件名是否以'R.stl'结尾
    elif filename.endswith('R.stl'):
        # 如果是，将'R.stl'替换为'L.stl'
        return filename.replace('R.stl', 'L.stl')


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
                print("左耳文件存在")
                context.scene.leftEar_path = example_l_path
            else:
                print("左耳文件不存在")


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
                print("右耳文件存在")
                context.scene.rightEar_path = example_r_path
            else:
                print("右耳文件不存在")


def qiegeenum(self, context):
    bl_description = "选择切割方式"
    enum = bpy.context.scene.qieGeTypeEnum
    if enum == "OP1":
        quitStepCut()
        override = getOverride()
        with bpy.context.temp_override(**override):
            initCircle()
    if enum == "OP2":
        quitCut()
        override = getOverride()
        with bpy.context.temp_override(**override):
            initPlane()


def qiegesmooth2(self, context):
    bl_description = "阶梯切割平滑偏移值2"
    pianyi = bpy.context.scene.qiegeneiBianYuan
    bpy.data.objects["StepCutplane"].modifiers["smooth"].width = pianyi


# 回调函数，根据绑定的属性值更改选中区域的厚度


def LocalThickeningOffsetUpdate(self, context):
    bl_description = "更新选中区域中加厚的厚度"

    offset = context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
    borderWidth = context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
    is_thickening_completed = context.scene.is_thickening_completed  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变

    if (not is_thickening_completed):
        if (True):  # TODO   当处于加厚未提交时,参数发生变化才会调用加厚函数

            # 根据更新后的参数重新进行加厚
            context.scene.is_thickening_completed = True
            thickening_offset_borderwidth(0, 0, True)
            thickening_offset_borderwidth(offset, borderWidth, False)
            context.scene.is_thickening_completed = False
    else:
        pass


def LocalThickeningBorderWidthUpdate(self, context):
    bl_description = "更新选中区域中的过渡区域"

    offset = context.scene.localThicking_offset  # 获取局部加厚面板中的偏移量参数
    borderWidth = context.scene.localThicking_borderWidth  # 获取局部加厚面板中的边界宽度参数
    is_thickening_completed = context.scene.is_thickening_completed  # 局部加厚是否已经完成,防止参数更新过快使得模型加厚发生形变

    if (not is_thickening_completed):
        if (True):  # TODO   当处于加厚未提交时,参数发生变化才会调用加厚函数
            # 根据更新后的参数重新进行加厚
            context.scene.is_thickening_completed = True
            thickening_offset_borderwidth(0, 0, True)
            thickening_offset_borderwidth(offset, borderWidth, False)
            context.scene.is_thickening_completed = False

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
    with bpy.context.temp_override(**override):
        recover_flag = recover()
        if enum == "OP1":
            print("软耳模")
            apply_soft_eardrum_template()
            convert_to_mesh('BottomRingBorderR',0.3)
        if enum == "OP2":
            print("硬耳膜")
        if enum == "OP3":
            print("一体外壳")
        if enum == "OP4":
            print("框架式耳膜")
            apply_frame_style_eardrum_template()
            convert_to_mesh('BottomRingBorderR',0.4)
            convert_to_mesh('HoleBorderCurveR', 0.18)
        if enum == "OP5":
            print("常规外壳")
        if enum == "OP6":
            print("实心面板")


def CreateMouldThicknessUpdate(self, context):
    bl_description = "更新创建模具中的总厚度"
    thickness = context.scene.zongHouDu

    # todo 根据不同的模具执行不同的逻辑
    override = getOverride()
    with bpy.context.temp_override(**override):
        reset_and_refill()


def CreateMouldOuterSmooth(self, context):
    bl_description = "创建模具后,平滑其外边缘"

    obj = bpy.data.objects["右耳"]
    smooth = round(bpy.context.scene.waiBianYuanSheRuPianYi, 1)

    override = getOverride()
    with bpy.context.temp_override(**override):
        modifier_name = "Smooth"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:  # TODO  优化：   将创建修改器放到加厚的invoke中，应用修改器放到提交中
                target_modifier = modifier
        if (target_modifier != None):
            bpy.context.object.modifiers["Smooth"].iterations = int(smooth * 10)


def CreateMouldInnerSmooth(self, context):
    bl_description = "创建模具后,平滑其内边缘"

    obj = bpy.data.objects["右耳"]
    smooth = round(bpy.context.scene.neiBianYuanSheRuPianYi, 1)

    override = getOverride()
    with bpy.context.temp_override(**override):
        modifier_name = "Smooth.001"
        target_modifier = None
        for modifier in obj.modifiers:
            if modifier.name == modifier_name:  # TODO  优化：   将创建修改器放到加厚的invoke中，应用修改器放到提交中
                target_modifier = modifier
        if (target_modifier != None):
            bpy.context.object.modifiers["Smooth.001"].iterations = int(smooth * 10)


def LabelTextUpdate(self, context):
    bl_description = "更新标签中的文本内容"

    print("update")
    labelText = bpy.context.scene.labelText

    # 将属性面板中的text属性值读取到剪切板中生成新的label
    override = getOverride()
    with bpy.context.temp_override(**override):
        labelTextUpdate(labelText)


def LabelSizeUpdate(self, context):
    bl_description = "更新文本中字体的大小"
    size = bpy.context.scene.fontSize
    print("字体大小更新")
    override = getOverride()
    with bpy.context.temp_override(**override):
        labelSizeUpdate(size)


def LabelDepthUpdate(self, context):
    bl_description = "更新文本中字体的高度"
    depth = bpy.context.scene.deep
    override = getOverride()
    with bpy.context.temp_override(**override):
        labelDepthUpdate(depth)


def LabelEnum(self, context):
    bl_description = "切换Label的类型风格"
    enum = bpy.context.scene.styleEnum
    if enum == "OP1":
        override = getOverride()
        with bpy.context.temp_override(**override):
            textname = "Text"
            text_obj = bpy.data.objects[textname]
            planename = "Plane"
            plane_obj = bpy.data.objects[planename]
            bpy.context.view_layer.objects.active = text_obj
            red_material = bpy.data.materials.new(name="Red")
            red_material.diffuse_color = (1.0, 0.0, 0.0, 1.0)
            text_obj.data.materials.clear()
            text_obj.data.materials.append(red_material)
            bpy.context.view_layer.objects.active = plane_obj
    if enum == "OP2":
        override = getOverride()
        with bpy.context.temp_override(**override):
            textname = "Text"
            text_obj = bpy.data.objects[textname]
            planename = "Plane"
            plane_obj = bpy.data.objects[planename]
            bpy.context.view_layer.objects.active = text_obj
            red_material = bpy.data.materials.new(name="Blue")
            red_material.diffuse_color = (0, 0.4, 1, 1.0)
            text_obj.data.materials.clear()
            text_obj.data.materials.append(red_material)
            bpy.context.view_layer.objects.active = plane_obj

def SupportEnum(self, context):

    bl_description = "切换支撑的类型"

    enum = bpy.context.scene.zhiChengTypeEnum
    #添加硬耳膜支撑
    if enum == "OP1":
        override = getOverride()
        with bpy.context.temp_override(**override):
            supportSaveInfo()
            supportReset()    
            # supportInitial()
            print("切换到硬耳膜支撑")

    #添加软耳膜支撑 
    if enum == "OP2":
        override = getOverride()
        with bpy.context.temp_override(**override):
            supportSaveInfo()
            supportReset()
            # supportInitial()
            print("切换到软耳膜支撑")


def SupportOffsetUpdate(self, context):

    bl_description = "更新支撑沿法线的偏移值"

    offset = bpy.context.scene.zhiChengOffset
    override = getOverride()
    with bpy.context.temp_override(**override):
        print("offset更新")

def register():
    My_Properties()


